pipeline {

    agent any

    parameters {

        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Deployment operation'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['UAT', 'PRODUCTION'],
            description: 'Target environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Git tag/version, e.g. 4.2.1 or 4.2.2'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Required YES for production deployment'
        )
    }

    environment {

        APP_NAME = 'retail-app'
        NETWORK = 'retail-network'
        HOST_PORT = '8081'
        CANDIDATE_PORT = '18081'
        CONTAINER_PORT = '8081'
        STATE_FILE = 'previous-production-image.txt'
    }

    stages {

        stage('Validate Parameters') {
            steps {
                script {

                    if (
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                        params.CONFIRM_PROD != 'YES'
                    ) {
                        error(
                            'PRODUCTION deployment blocked: CONFIRM_PROD must be YES'
                        )
                    }

                    if (!(params.VERSION ==~ /[0-9]+\.[0-9]+\.[0-9]+/)) {
                        error("Invalid VERSION: ${params.VERSION}")
                    }
                }
            }
        }

        stage('Checkout and Identify Commit') {
            steps {

                checkout scm

                bat 'git rev-parse HEAD > selected-commit.txt'

                bat 'type selected-commit.txt'
            }
        }

        stage('Validate Git Version') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                bat 'git rev-parse "refs/tags/v%VERSION%"'

            }
        }

        stage('Unit Tests') {

            steps {

                bat 'where python'

                bat 'python -m pip install -r requirements.txt'

                bat 'python -m pytest -q'
            }
        }

        stage('Build Versioned Image') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                script {

                    env.IMAGE =
                        "${APP_NAME}:${params.VERSION}-${env.BUILD_NUMBER}"

                    env.CANDIDATE =
                        "${APP_NAME}-candidate-${env.BUILD_NUMBER}"
                }

                bat 'docker build -t %IMAGE% .'
            }
        }

        stage('Record Previous Production Image') {

            when {

                allOf {

                    expression {
                        params.DEPLOYMENT_ACTION == 'DEPLOY'
                    }

                    expression {
                        params.ENVIRONMENT == 'PRODUCTION'
                    }
                }
            }

            steps {

                script {

                    int rc = bat(
                        returnStatus: true,
                        script: 'docker ps --filter "name=retail-app-prod" --format "{{.Image}}" > previous-production-image.txt'
                    )

                    if (rc != 0) {
                        error('Could not determine current production image.')
                    }

                    bat 'echo Previous production image:'

                    bat 'type previous-production-image.txt'

                    script {

                        def previousImage =
                            readFile('previous-production-image.txt').trim()

                        if (!previousImage) {

                            error(
                                'No running production image found. Cannot safely deploy to production.'
                            )
                        }

                        env.PREVIOUS_IMAGE = previousImage

                        echo "Previous production image = ${env.PREVIOUS_IMAGE}"
                    }
                }
            }
        }

        stage('Start Candidate') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                script {

                    /*
                     * Mandatory failure injection.
                     *
                     * Version 4.2.2 deliberately returns HTTP 500
                     * from /health.
                     */

                    env.FAIL_HEALTH =
                        (params.VERSION == '4.2.2')
                        ? 'true'
                        : 'false'
                }

                bat 'echo FAIL_HEALTH=%FAIL_HEALTH%'

                bat '''
                    docker network inspect %NETWORK% >nul 2>&1 || docker network create %NETWORK%
                '''

                bat '''
                    docker rm -f %CANDIDATE% >nul 2>&1 || exit /b 0
                '''

                bat '''
                    docker run -d ^
                    --name %CANDIDATE% ^
                    --memory 512m ^
                    --cpus 0.5 ^
                    --network %NETWORK% ^
                    -p %CANDIDATE_PORT%:%CONTAINER_PORT% ^
                    -e APP_VERSION=%VERSION% ^
                    -e ENVIRONMENT=%ENVIRONMENT% ^
                    -e PAYMENT_MODE=fixed ^
                    -e FAIL_HEALTH=%FAIL_HEALTH% ^
                    %IMAGE%
                '''
            }
        }

        stage('Candidate Container Validation') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                bat 'docker ps --filter "name=%CANDIDATE%"'

                bat '''
                    docker inspect --format "{{.State.Status}}" %CANDIDATE%
                '''
            }
        }

        stage('Health Check') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                script {

                    int attempts = 10
                    boolean healthy = false

                    for (int i = 1; i <= attempts; i++) {

                        echo "Health check attempt ${i}/${attempts}"

                        int rc = bat(
                            returnStatus: true,
                            script: 'curl.exe -fsS http://localhost:%CANDIDATE_PORT%/health > health-response.json'
                        )

                        if (rc == 0) {

                            healthy = true

                            echo 'Candidate health check PASSED.'

                            break
                        }

                        sleep time: 3, unit: 'SECONDS'
                    }

                    if (!healthy) {

                        error(
                            'Health check failed. Automatic rollback protection will execute.'
                        )
                    }
                }
            }
        }

        stage('Promote Candidate') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                echo 'Candidate passed validation.'

                echo 'Promoting validated candidate to production.'

                bat '''
                    docker rm -f retail-app-prod >nul 2>&1 || exit /b 0
                '''

                bat '''
                    docker rm -f %CANDIDATE% >nul 2>&1 || exit /b 0
                '''

                bat '''
                    docker run -d ^
                    --name retail-app-prod ^
                    --memory 512m ^
                    --cpus 0.5 ^
                    --network %NETWORK% ^
                    -p %HOST_PORT%:%CONTAINER_PORT% ^
                    -e APP_VERSION=%VERSION% ^
                    -e ENVIRONMENT=%ENVIRONMENT% ^
                    -e PAYMENT_MODE=fixed ^
                    -e FAIL_HEALTH=false ^
                    %IMAGE%
                '''

                bat '''
                    powershell -NoProfile -Command "Start-Sleep -Seconds 15"
                '''

                bat '''
                    docker inspect --format "{{.State.Health.Status}}" retail-app-prod
                '''

                bat '''
                    curl.exe -fsS http://localhost:%HOST_PORT%/health
                '''
            }
        }

        stage('Manual Rollback') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {

                script {

                    def previousImage =
                        fileExists(env.STATE_FILE)
                        ? readFile(env.STATE_FILE).trim()
                        : ''

                    if (!previousImage) {
                        error(
                            'Rollback requested but previous-production-image.txt is empty or missing.'
                        )
                    }

                    echo "Restoring previous production image: ${previousImage}"

                    bat '''
                        docker rm -f retail-app-prod >nul 2>&1 || exit /b 0
                    '''

                    bat """
                        docker run -d ^
                        --name retail-app-prod ^
                        --memory 512m ^
                        --cpus 0.5 ^
                        --network %NETWORK% ^
                        -p %HOST_PORT%:%CONTAINER_PORT% ^
                        -e APP_VERSION=4.2.1 ^
                        -e ENVIRONMENT=PRODUCTION ^
                        -e PAYMENT_MODE=fixed ^
                        -e FAIL_HEALTH=false ^
                        ${previousImage}
                    """
                }
            }
        }

        stage('Rollback Validation') {

            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {

                bat '''
                    powershell -NoProfile -Command "Start-Sleep -Seconds 15"
                '''

                bat '''
                    docker inspect --format "{{.State.Health.Status}}" retail-app-prod
                '''

                bat '''
                    curl.exe -fsS http://localhost:%HOST_PORT%/health
                '''

                echo 'Manual rollback validation passed.'
            }
        }
    }

    post {

        failure {

            script {

                if (params.DEPLOYMENT_ACTION == 'DEPLOY') {

                    echo '============================================'
                    echo 'DEPLOYMENT FAILED'
                    echo 'AUTOMATIC ROLLBACK PROTECTION STARTED'
                    echo '============================================'

                    /*
                     * Always remove the failed candidate.
                     */

                    bat '''
                        docker rm -f %CANDIDATE% >nul 2>&1 || exit /b 0
                    '''

                    /*
                     * For production:
                     *
                     * The old production container was intentionally
                     * kept alive until candidate validation succeeded.
                     *
                     * If production is unhealthy, restore the
                     * previously recorded image.
                     */

                    if (params.ENVIRONMENT == 'PRODUCTION') {

                        echo 'Production deployment failed.'

                        script {

                            int productionHealth = bat(
                                returnStatus: true,
                                script: 'curl.exe -fsS http://localhost:%HOST_PORT%/health >nul 2>&1'
                            )

                            if (productionHealth == 0) {

                                echo 'Existing production container is still healthy.'
                                echo 'No production restoration was required.'
                                echo "Previous production image was: ${env.PREVIOUS_IMAGE ?: 'not available'}"

                            } else {

                                echo 'Existing production is unhealthy.'
                                echo 'Restoring previous production image.'

                                def previousImage =
                                    fileExists(env.STATE_FILE)
                                    ? readFile(env.STATE_FILE).trim()
                                    : ''

                                if (!previousImage) {

                                    error(
                                        'Automatic rollback failed: previous production image is unavailable.'
                                    )
                                }

                                bat '''
                                    docker rm -f retail-app-prod >nul 2>&1 || exit /b 0
                                '''

                                bat """
                                    docker run -d ^
                                    --name retail-app-prod ^
                                    --memory 512m ^
                                    --cpus 0.5 ^
                                    --network %NETWORK% ^
                                    -p %HOST_PORT%:%CONTAINER_PORT% ^
                                    -e APP_VERSION=4.2.1 ^
                                    -e ENVIRONMENT=PRODUCTION ^
                                    -e PAYMENT_MODE=fixed ^
                                    -e FAIL_HEALTH=false ^
                                    ${previousImage}
                                """

                                bat '''
                                    powershell -NoProfile -Command "Start-Sleep -Seconds 15"
                                '''

                                bat '''
                                    docker inspect --format "{{.State.Health.Status}}" retail-app-prod
                                '''

                                bat '''
                                    curl.exe -fsS http://localhost:%HOST_PORT%/health
                                '''

                                echo 'Automatic rollback restoration completed successfully.'
                            }
                        }
                    }

                    echo '============================================'
                    echo 'ROLLBACK PROTECTION COMPLETED'
                    echo 'FINAL JENKINS RESULT = FAILURE'
                    echo '============================================'
                }
            }
        }

        always {

            bat '''
                docker ps -a --filter "name=retail-app"
            '''

            bat '''
                docker images retail-app
            '''
        }

        success {

            echo 'Deployment completed and validated successfully.'
        }
    }
}
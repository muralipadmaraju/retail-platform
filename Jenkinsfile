pipeline {
    agent any

    parameters {
        choice(name: 'DEPLOYMENT_ACTION', choices: ['DEPLOY', 'ROLLBACK'], description: 'Deployment operation')
        choice(name: 'ENVIRONMENT', choices: ['UAT', 'PRODUCTION'], description: 'Target environment')
        string(name: 'VERSION', defaultValue: '4.2.1', description: 'Git tag/version, e.g. 4.2.1 or 4.2.2')
        choice(name: 'CONFIRM_PROD', choices: ['NO', 'YES'], description: 'Required YES for production deployment')
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
                    if (params.ENVIRONMENT == 'PRODUCTION' && params.DEPLOYMENT_ACTION == 'DEPLOY' && params.CONFIRM_PROD != 'YES') {
                        error('PRODUCTION deployment blocked: CONFIRM_PROD must be YES')
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
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                bat 'git rev-parse "refs/tags/v%VERSION%"'
            }
        }

        stage('Unit Tests') {
            steps {
                bat '"C:\Users\Administrator\AppData\Local\Python\bin\python.exe" -m pip install -r requirements.txt'
bat '"C:\Users\Administrator\AppData\Local\Python\bin\python.exe" -m pytest -q'
            }
        }

        stage('Build Versioned Image') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                script {
                    env.IMAGE = "${APP_NAME}:${params.VERSION}-${env.BUILD_NUMBER}"
                    env.CANDIDATE = "${APP_NAME}-candidate-${env.BUILD_NUMBER}"
                }
                bat 'docker build -t %IMAGE% .'
            }
        }

        stage('Record Previous Production Image') {
            when {
                allOf {
                    expression { params.DEPLOYMENT_ACTION == 'DEPLOY' }
                    expression { params.ENVIRONMENT == 'PRODUCTION' }
                }
            }
            steps {
                bat 'docker ps --filter "name=retail-app-prod" --format "{{.Image}}" > previous-production-image.txt'
                bat 'if not exist previous-production-image.txt type nul > previous-production-image.txt'
                bat 'echo Previous production image: & type previous-production-image.txt'
            }
        }

        stage('Start Candidate') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                script {
                    // Mandatory failure injection: v4.2.2 starts normally but its health endpoint returns 500.
                    env.FAIL_HEALTH = (params.VERSION == '4.2.2') ? 'true' : 'false'
                }
                bat 'echo Failure injection FAIL_HEALTH=%FAIL_HEALTH%'
                bat 'docker network inspect %NETWORK% >nul 2>&1 || docker network create %NETWORK%'
                bat 'docker rm -f %CANDIDATE% >nul 2>&1 || exit /b 0'
                bat 'docker run -d --name %CANDIDATE% --network %NETWORK% -p %CANDIDATE_PORT%:%CONTAINER_PORT% -e APP_VERSION=%VERSION% -e ENVIRONMENT=%ENVIRONMENT% -e PAYMENT_MODE=fixed -e FAIL_HEALTH=%FAIL_HEALTH% %IMAGE%'
            }
        }

        stage('Candidate Container Validation') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                bat 'docker ps --filter "name=%CANDIDATE%"'
                bat 'docker inspect --format "{{.State.Status}}" %CANDIDATE%'
            }
        }

        stage('Health Check') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                script {
                    int attempts = 10
                    boolean healthy = false
                    for (int i = 1; i <= attempts; i++) {
                        echo "Health check attempt ${i}/${attempts}"
                        int rc = bat(returnStatus: true, script: 'curl.exe -fsS http://localhost:%CANDIDATE_PORT%/health > health-response.json')
                        if (rc == 0) { healthy = true; break }
                        sleep time: 3, unit: 'SECONDS'
                    }
                    if (!healthy) {
                        error('Health check failed; automatic rollback will run in post/finally logic.')
                    }
                }
            }
        }

        stage('Promote Candidate') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                echo 'Candidate passed validation; switching production to the validated image.'
                bat 'docker rm -f retail-app-prod >nul 2>&1 || exit /b 0'
                bat 'docker rm -f %CANDIDATE% >nul 2>&1 || exit /b 0'
                bat 'docker run -d --name retail-app-prod --network %NETWORK% -p %HOST_PORT%:%CONTAINER_PORT% -e APP_VERSION=%VERSION% -e ENVIRONMENT=%ENVIRONMENT% -e PAYMENT_MODE=fixed -e FAIL_HEALTH=false %IMAGE%'
                bat 'docker inspect --format "{{.State.Health.Status}}" retail-app-prod'
                bat 'curl.exe -fsS http://localhost:%HOST_PORT%/health'
            }
        }

        stage('Rollback') {
            when { expression { params.DEPLOYMENT_ACTION == 'ROLLBACK' } }
            steps {
                bat 'if not exist previous-production-image.txt exit /b 1'
                bat 'for /f "delims=" %%I in (previous-production-image.txt) do docker run -d --name retail-app-prod --network %NETWORK% -p %HOST_PORT%:%CONTAINER_PORT% -e APP_VERSION=4.2.1 -e ENVIRONMENT=PRODUCTION -e PAYMENT_MODE=fixed %%I'
            }
        }

        stage('Rollback Validation') {
            when { expression { params.DEPLOYMENT_ACTION == 'ROLLBACK' } }
            steps {
                bat 'curl.exe -fsS http://localhost:%HOST_PORT%/health'
                bat 'docker inspect --format "{{.State.Health.Status}}" retail-app-prod'
                echo 'Rollback validation passed.'
            }
        }
    }

    post {
        failure {
            script {
                if (params.DEPLOYMENT_ACTION == 'DEPLOY') {
                    echo 'Deployment failed. Starting automatic rollback protection.'
                    bat 'docker rm -f %CANDIDATE% >nul 2>&1 || exit /b 0'
                    if (params.ENVIRONMENT == 'PRODUCTION') {
                        if (bat(returnStatus: true, script: 'curl.exe -fsS http://localhost:%HOST_PORT%/health >nul 2>&1') != 0) {
                            bat 'docker rm -f retail-app-prod >nul 2>&1 || exit /b 0'
                            bat 'if exist previous-production-image.txt for /f "delims=" %%I in (previous-production-image.txt) do docker run -d --name retail-app-prod --network %NETWORK% -p %HOST_PORT%:%CONTAINER_PORT% -e APP_VERSION=4.2.1 -e ENVIRONMENT=PRODUCTION -e PAYMENT_MODE=fixed %%I'
                        } else {
                            echo 'Previous production container is still healthy; no restoration was necessary.'
                        }
                    }
                    echo 'Rollback protection completed. Final Jenkins state remains FAILURE as required.'
                }
            }
        }
        always {
            bat 'docker ps -a --filter "name=retail-app"'
            bat 'docker images retail-app'
        }
        success {
            echo 'Deployment completed and validated successfully.'
        }
    }
}

pipeline {
    agent any

    environment {
        IMAGE_NAME = "ghcr.io/asalinao/telegram_chats_parser_app:latest"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/asalinao/telegram_chats_parser'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat "docker build -t %IMAGE_NAME% ."
            }
        }

        stage('Login to GHCR') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'jenkins-registry',
                    usernameVariable: 'GH_USERNAME',
                    passwordVariable: 'GH_TOKEN'
                )]) {
                    bat """
                    echo %GH_TOKEN% | docker login ghcr.io -u %GH_USERNAME% --password-stdin
                    """
                }
            }
        }

        stage('Push Image to GHCR') {
            steps {
                bat "docker push %IMAGE_NAME%"
            }
        }

        stage('Deploy to VM') {
            steps {
                sshagent(['vm-ssh-credentials-id']) {
                    sh """
                    ssh ${DEPLOY_HOST} '
                      cd ${DEPLOY_PATH} &&
                      docker-compose pull &&
                      docker-compose up -d --build
                    '
                    """
                }
            }
        }
    }
}
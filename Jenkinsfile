pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/asalinao/telegram_chats_parser'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t telegram_chats_parser_app:latest .'
            }
        }
    }
}

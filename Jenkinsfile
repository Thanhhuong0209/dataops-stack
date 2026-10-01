pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDENTIALS_ID = 'docker-hub-credentials'
        IMAGE_NAME = 'thanhhuong29/dagster-user-code'
        IMAGE_TAG = 'latest'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('', DOCKER_HUB_CREDENTIALS_ID) {
                        dockerImage.push()
                        dockerImage.push(IMAGE_TAG)
                    }
                }
            }
        }

        stage('Deploy to target host') {
            steps {
                script {
                    sh '''
                        docker compose down
                        docker compose pull
                        docker compose up -d
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Build and push completed successfully.'
        }
        failure {
            echo 'Build failed.'
        }
    }
}


pipeline {
    agent {
        kubernetes {
            cloud 'linux-amd64'
            defaultContainer 'python-node'
            yamlFile 'pod-definition.yaml'
        }
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
        timeout(time: 3, unit: 'HOURS')
        timestamps()
        ansiColor('xterm')
    }

    stages {
        stage('hooks') {
            environment {
                RPY2_CFFI_MODE = 'ABI'
            }
            steps {
                sh 'git config --global --add safe.directory $PWD'
                sh 'git status'
                dir('./src/honeyfront') {
                    sh 'npm install'
                }
                dir('./src/honeyback') {
                    sh 'poetry install --with hooks,analytics,docker'
                    sh 'poetry run pre-commit run --all-files'
                }
            }
        }

        stage('build') {
            environment {
                DOCKER_BUILDKIT = '1'
            }
            steps {
                container('docker') {
                    sh 'docker build -t honeyquest .'
                }
            }
        }
    }
}

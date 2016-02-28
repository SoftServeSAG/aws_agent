# AWS Agent
Simple AWS EC2 Spot Instance manager

## Prerequisites:
 - Python 3.4+
 - AWS Command Line Interface (CLI)
 - Boto3 framework
 - pytz, matplotlib 1.5+ (price statistics plotting only)

## Installation (Linux, OS X):
```bash
pip3 install boto3 awscli pytz
git clone https://github.com/Pebody/aws_agent
```

## Installation (Windows):
TBA

## Configuration:
 - Configure AWS CLI
http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html
 - Edit profile.ini file using the example provided

## Usage:
```bash
cd aws_agent
./aws_agent.py --help
```

# AWS Agent
Simple AWS EC2 Spot Instance manager


## Prerequisites:
 - Python 3.4+
 - AWS Command Line Interface (CLI)
 - Boto3 framework
 - pytz, matplotlib 1.5+ (price statistics plotting only)


## Installation (Linux, OS X):
Complete following steps (in Terminal):
```bash
pip3 install boto3 awscli pytz
git clone https://github.com/Pebody/aws_agent
```
Check official installation guides for the details ([this](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) and [this](http://boto3.readthedocs.org/en/latest/guide/quickstart.html))

## Installation (Windows):
TBA


## Configuration:
 - [Configure AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
 - Edit *profile.ini* file using the example provided


## Usage:
```bash
cd aws_agent
./aws_agent.py --help
```

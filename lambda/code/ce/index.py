import os
import pandas as pd
import matplotlib.pyplot as plt
import boto3
from botocore.config import Config
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from LoggingClass import LoggingClass


# ----------------------------------------------------------------------
# Environment Variable Setting
# ----------------------------------------------------------------------
try:
    SLACK_TOKEN = os.environ["SLACK_TOKEN"]
    CHANNEL_ID = os.environ["CHANNEL_ID"]
except KeyError:
    raise Exception("Environment variable is not defined.")

# ----------------------------------------------------------------------
# Global Variable Setting
# ----------------------------------------------------------------------
try:
    config = Config(
        retries={"max_attempts": 30, "mode": "standard"},
        read_timeout=900,
        connect_timeout=900,
    )
    bedrock_client = boto3.client("bedrock-runtime", config=config)
    s3_client = boto3.client("s3", config=config)
    slack_client = WebClient(token=SLACK_TOKEN)
except Exception:
    raise Exception("Boto3 client error")

# ----------------------------------------------------------------------
# Logger Setting
# ----------------------------------------------------------------------
try:
    logger = LoggingClass("DEBUG")
    log = logger.get_logger()
except Exception:
    raise Exception("Logger Setting failed")


# ----------------------------------------------------------------------
# Main Function
# ----------------------------------------------------------------------
def main(event):
    try:
        send_slack()
        response = {"statusCode": 200}
        return response
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise


# ----------------------------------------------------------------------
# Slack Message
# ----------------------------------------------------------------------
def send_slack():
    try:
        # response = slack_client.chat_postMessage(
        #     username="CostExplorer",
        #     icon_url="https://www.metalmental.net/images/CostExplorer.png",
        #     channel=CHANNEL_ID,
        #     text="Hello world!",
        # )
        # assert response["message"]["text"] == "Hello world!"

        # データの作成
        data = {"x": [1, 2, 3, 4, 5], "y": [2, 3, 5, 7, 11]}
        df = pd.DataFrame(data)
        # グラフの作成
        plt.plot(df["x"], df["y"])
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title("matplotlib")
        # グラフを画像として保存
        plt.savefig("/tmp/plot.png")
        response = slack_client.files_upload_v2(
            channel=CHANNEL_ID,
            title="CostExplorer",
            file="/tmp/plot.png",
            initial_comment="CostExplorer コスト通知",
        )
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise


# ----------------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------------
def lambda_handler(event: dict, context):
    try:
        log.debug(f"event: {event}")
        response = main(event)
        return response
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise

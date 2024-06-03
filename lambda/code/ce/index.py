import os
import boto3
from datetime import datetime, timedelta
from botocore.config import Config

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import matplotlib.pyplot as plt

# import pandas as pd
# import numpy as np

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
    ce_client = boto3.client("ce", config=config)
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
def main():
    try:
        formatted_data = get_cost()
        cost_img = create_cost_img(formatted_data)
        send_slack(cost_img)
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise


# ----------------------------------------------------------------------
# Get Cost
# ----------------------------------------------------------------------
def get_cost():
    try:
        # Calculate costs for 7 days
        today = datetime.today()
        seven_days_ago = today - timedelta(days=7)
        today = today.strftime("%Y-%m-%d")
        seven_days_ago = seven_days_ago.strftime("%Y-%m-%d")

        request_parameter = {
            "TimePeriod": {
                "Start": seven_days_ago,
                "End": today,
            },
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE",
                },
            ],
        }

        # formatted_data = {
        #     "day1": {
        #         "service1": "cost1",
        #         "service2": "cost2",
        #     },
        #     "day2": {
        #         "service1": "cost1",
        #         "service2": "cost2",
        #     },
        # }

        response_list = []
        formatted_data = {}
        response = ce_client.get_cost_and_usage(**request_parameter)
        response_list.extend(response["ResultsByTime"])
        while "NextToken" in response:
            response = ce_client.get_cost_and_usage(**request_parameter, NextPageToken=response["NextToken"])
            response_list.extend(response["ResultsByTime"])
        for i in response_list:
            day = i["TimePeriod"]["Start"]
            day = day.replace("-", "/")
            day = day[5:]
            day_service_cost_dict = {}
            cost_sorted_groups = sorted(i["Groups"], key=lambda x: float(x["Metrics"]["UnblendedCost"]["Amount"]), reverse=True)[:7]
            for j in cost_sorted_groups:
                if j["Keys"][0] != "Tax" and j["Keys"][0] != "AWS Support (Developer)":
                    day_service_cost_dict[j["Keys"][0]] = j["Metrics"]["UnblendedCost"]["Amount"]
            formatted_data[day] = day_service_cost_dict
        log.debug(formatted_data)

        return formatted_data
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise


# ----------------------------------------------------------------------
# Stacked vertical bar graph with an image
# ----------------------------------------------------------------------
def create_cost_img(key_amount_dict_sort):
    try:
        # formatted_data = {
        #     "day1": {
        #         "service1": "cost1",
        #         "service2": "cost2",
        #     },
        #     "day2": {
        #         "service1": "cost1",
        #         "service2": "cost2",
        #     },
        # }

        # Convert costs (strings) to costs (float) by service
        for day in key_amount_dict_sort:
            for service in key_amount_dict_sort[day]:
                key_amount_dict_sort[day][service] = float(key_amount_dict_sort[day][service])

        # costs_by_service (Empty values are set at 0)
        # {
        #     'service_a': [100, 150, 0],
        #     'service_b': [200, 0, 250],
        #     'service_c': [0, 300, 0],
        #     'service_d': [0, 0, 400]
        # }

        # Create a list of dates, services and costs
        days = list(key_amount_dict_sort.keys())
        services = list({service for day in key_amount_dict_sort.values() for service in day.keys()})
        costs_by_service = {service: [key_amount_dict_sort[day].get(service, 0) for day in days] for service in services}
        sorted_costs_by_service = dict(sorted(costs_by_service.items(), key=lambda item: sum(item[1]), reverse=True))
        log.debug(f"Days: {days}")
        log.debug(f"Services: {services}")
        log.debug(f"Cost by services 7-day dict: {sorted_costs_by_service}")

        plt.figure(figsize=(10, 6))  # Set the size of the graph
        plt.rcParams["axes.prop_cycle"] = plt.cycler("color", plt.get_cmap("Pastel1").colors)  # Colour of graph
        bottom = [0] * len(days)  # Initialise the base of the bar with 0
        for service in sorted_costs_by_service:
            costs = sorted_costs_by_service[service]
            plt.bar(days, costs, bottom=bottom, label=service)  # Draw the dayly bar graph
            bottom = [b + c for b, c in zip(bottom, costs)]  # Add the height of the BAR at cost

        # Set the label
        plt.xlabel("Day")
        plt.ylabel("Cost\n (USD)\n", rotation="horizontal")
        plt.ylim(0, max(bottom) * 1.2)
        plt.title("Cost in the last week")
        plt.legend(loc="upper left", bbox_to_anchor=(1, 1))  # Label position
        plt.tight_layout()

        # Save the graph as an image
        cost_img = "/tmp/cost_by_service_and_date.png"
        plt.savefig(cost_img)

        return cost_img
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise


# ----------------------------------------------------------------------
# Send an image to Slack
# ----------------------------------------------------------------------
def send_slack(cost_img):
    try:
        # response = slack_client.chat_postMessage(
        #     username="CostExplorer",
        #     icon_url="https://www.metalmental.net/images/CostExplorer.png",
        #     channel=CHANNEL_ID,
        #     text="Hello world!",
        # )
        # assert response["message"]["text"] == "Hello world!"

        slack_client.files_upload_v2(
            channel=CHANNEL_ID,
            title="CostExplorer",
            file=cost_img,
            initial_comment="CostExplorer コスト通知",
        )
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise


# ----------------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------------
def lambda_handler(event, context):
    try:
        main()
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        raise

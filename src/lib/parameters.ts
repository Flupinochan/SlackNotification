export class Parameters {
  env = {
    region: "ap-northeast-1",
  };
  lambdaCommon = {
    roleName: "SlackNotification-LambdaRole",
    layerName: "SlackNotification-LambdaLayer",
    layerDesciption: "SlackNotification Lambda Layer",
  }
  lambdaCE = {
    logGroupName: "SlackNotification-LambdaCE-Log",
    functionName: "SlackNotification-LambdaCE",
    eventBridgeName: "SlackNotification-LambdaCE-EventBridge",
  }
}
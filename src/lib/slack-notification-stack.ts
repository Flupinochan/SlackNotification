import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Duration } from "aws-cdk-lib";
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as path from 'path';

import {Parameters} from "../lib/parameters";

const param = new Parameters();

export class SlackNotificationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const lambdaRole = new iam.Role(this, param.lambdaCommon.roleName, {
      roleName: param.lambdaCommon.roleName,
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchFullAccessV2'),
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonS3FullAccess"),
      ],
      inlinePolicies: {
        "CostExplorerAccess": new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                "ce:*",
              ],
              resources: ["*"],
            }),
          ],
        }),
      },
    });
    const lambdaCE_LogGroup = new logs.LogGroup(this, param.lambdaCE.logGroupName, {
      logGroupName: param.lambdaCE.logGroupName,
      retention: logs.RetentionDays.ONE_DAY,
      logGroupClass: logs.LogGroupClass.STANDARD,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    // 外部ライブラリpandas利用方法
    // https://github.com/keithrozario/Klayers/tree/master/deployments/python3.12
    const lambdaCE = new lambda.DockerImageFunction(this, param.lambdaCE.functionName, {
      functionName: param.lambdaCE.functionName,
      role: lambdaRole,
      code: lambda.DockerImageCode.fromImageAsset(path.join(__dirname, "../../lambda/code/")),
      timeout: Duration.minutes(15),
      logGroup: lambdaCE_LogGroup,
      environment: {
        SLACK_TOKEN: "",
        CHANNEL_ID: "C07606G903F",
      },
    });
    const eventBridgeLambdaCE = new events.Rule(this, param.lambdaCE.eventBridgeName, {
      ruleName: param.lambdaCE.eventBridgeName,
      schedule: events.Schedule.cron({ minute: '0', hour: '9', weekDay: 'SUN' }),
      targets: [new targets.LambdaFunction(lambdaCE)]
    });
    lambdaCE.addPermission("SlackNotificationPermission", {
      principal: new iam.ServicePrincipal("events.amazonaws.com"),
      sourceArn: eventBridgeLambdaCE.ruleArn
    })

  }
}

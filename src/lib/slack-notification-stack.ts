import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Duration } from "aws-cdk-lib";
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
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
    const lambdaLayer = new lambda.LayerVersion(this, param.lambdaCommon.layerName, {
      layerVersionName: param.lambdaCommon.layerName,
      description: param.lambdaCommon.layerDesciption,
      code: lambda.Code.fromAsset(path.join(__dirname, "../../lambda/layer/")),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    const lambdaCE_LogGroup = new logs.LogGroup(this, param.lambdaCE.logGroupName, {
      logGroupName: param.lambdaCE.logGroupName,
      retention: logs.RetentionDays.ONE_DAY,
      logGroupClass: logs.LogGroupClass.STANDARD,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    // 外部ライブラリpandas利用方法
    // https://github.com/keithrozario/Klayers/tree/master/deployments/python3.12
    // const lambdaCE = new lambda.Function(this, param.lambdaCE.functionName, {
    //   functionName: param.lambdaCE.functionName,
    //   runtime: lambda.Runtime.PYTHON_3_12,
    //   handler: "index.lambda_handler",
    //   role: lambdaRole,
    //   code: lambda.Code.fromAsset(path.join(__dirname, "../../lambda/code/ce/")),
    //   timeout: Duration.minutes(15),
    //   logGroup: lambdaCE_LogGroup,

    //   // layers: [
    //   //   lambdaLayer,
    //   //   lambda.LayerVersion.fromLayerVersionArn(this, "pandas_layer", "ARN"),
    //   //   lambda.LayerVersion.fromLayerVersionArn(this, "matplotlib_layer", "ARN"),
    //   // ],
    //   environment: {
    //     SLACK_TOKEN: "xxxxx",
    //     CHANNEL_NAME: "#aws-cost-explorer",
    //   },
    // });
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

  }
}

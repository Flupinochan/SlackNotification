#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';

import { SlackNotificationStack } from '../lib/slack-notification-stack';
import {Parameters} from '../lib/parameters';

const param = new Parameters();

const app = new cdk.App();
new SlackNotificationStack(app, 'SlackNotificationStack', {
  env: { region: param.env.region}
});
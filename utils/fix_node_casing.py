#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrigiert die Groß-/Kleinschreibung der Node-Types
Verwendet die korrekte camelCase-Schreibweise aus GitHub anstatt lowercase aus der Doku
"""

import sys
import io
import sqlite3
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mapping von lowercase (Doku) zu camelCase (GitHub/Workflows)
# Basierend auf den GitHub .node.json Dateien
CORRECT_CASING = {
    # Action Network
    "n8n-nodes-base.actionnetwork": "n8n-nodes-base.actionNetwork",

    # ActiveCampaign
    "n8n-nodes-base.activecampaign": "n8n-nodes-base.activeCampaign",
    "n8n-nodes-base.activecampaigntrigger": "n8n-nodes-base.activeCampaignTrigger",

    # Acuity Scheduling
    "n8n-nodes-base.acuityschedulingtrigger": "n8n-nodes-base.acuitySchedulingTrigger",

    # Affinity
    "n8n-nodes-base.affinitytrigger": "n8n-nodes-base.affinityTrigger",

    # Agile CRM
    "n8n-nodes-base.agilecrm": "n8n-nodes-base.agileCrm",

    # AI Transform
    "n8n-nodes-base.aitransform": "n8n-nodes-base.aiTransform",

    # Airtable
    "n8n-nodes-base.airtabletrigger": "n8n-nodes-base.airtableTrigger",

    # AMQP
    "n8n-nodes-base.amqptrigger": "n8n-nodes-base.amqpTrigger",

    # API Template
    "n8n-nodes-base.apitemplateio": "n8n-nodes-base.apiTemplateIo",

    # Asana
    "n8n-nodes-base.asanatrigger": "n8n-nodes-base.asanaTrigger",

    # Autopilot
    "n8n-nodes-base.autopilottrigger": "n8n-nodes-base.autopilotTrigger",

    # AWS
    "n8n-nodes-base.awslambda": "n8n-nodes-base.awsLambda",
    "n8n-nodes-base.awssns": "n8n-nodes-base.awsSns",
    "n8n-nodes-base.awssnstrigger": "n8n-nodes-base.awsSnsTrigger",
    "n8n-nodes-base.awscertificatemanager": "n8n-nodes-base.awsCertificateManager",
    "n8n-nodes-base.awscognito": "n8n-nodes-base.awsCognito",
    "n8n-nodes-base.awscomprehend": "n8n-nodes-base.awsComprehend",
    "n8n-nodes-base.awsdynamodb": "n8n-nodes-base.awsDynamoDb",
    "n8n-nodes-base.awselb": "n8n-nodes-base.awsElb",
    "n8n-nodes-base.awsiam": "n8n-nodes-base.awsIam",
    "n8n-nodes-base.awsrekognition": "n8n-nodes-base.awsRekognition",
    "n8n-nodes-base.awss3": "n8n-nodes-base.awsS3",
    "n8n-nodes-base.awsses": "n8n-nodes-base.awsSes",
    "n8n-nodes-base.awssqs": "n8n-nodes-base.awsSqs",
    "n8n-nodes-base.awstextract": "n8n-nodes-base.awsTextract",
    "n8n-nodes-base.awstranscribe": "n8n-nodes-base.awsTranscribe",

    # Azure
    "n8n-nodes-base.azurecosmosdb": "n8n-nodes-base.azureCosmosDb",
    "n8n-nodes-base.azurestorage": "n8n-nodes-base.azureStorage",

    # BambooHR
    "n8n-nodes-base.bamboohr": "n8n-nodes-base.bambooHr",

    # Bitbucket
    "n8n-nodes-base.bitbuckettrigger": "n8n-nodes-base.bitbucketTrigger",

    # Box
    "n8n-nodes-base.boxtrigger": "n8n-nodes-base.boxTrigger",

    # Brevo
    "n8n-nodes-base.brevotrigger": "n8n-nodes-base.brevoTrigger",

    # Cal
    "n8n-nodes-base.caltrigger": "n8n-nodes-base.calTrigger",

    # Calendly
    "n8n-nodes-base.calendlytrigger": "n8n-nodes-base.calendlyTrigger",

    # Chargebee
    "n8n-nodes-base.chargebeetrigger": "n8n-nodes-base.chargebeeTrigger",

    # CircleCI
    "n8n-nodes-base.circleci": "n8n-nodes-base.circleCi",

    # Cisco Webex
    "n8n-nodes-base.ciscowebex": "n8n-nodes-base.ciscoWebex",
    "n8n-nodes-base.ciscowebextrigger": "n8n-nodes-base.ciscoWebexTrigger",

    # ClickUp
    "n8n-nodes-base.clickup": "n8n-nodes-base.clickUp",
    "n8n-nodes-base.clickuptrigger": "n8n-nodes-base.clickUpTrigger",

    # Clockify
    "n8n-nodes-base.clockifytrigger": "n8n-nodes-base.clockifyTrigger",

    # CoinGecko
    "n8n-nodes-base.coingecko": "n8n-nodes-base.coinGecko",

    # ConvertKit
    "n8n-nodes-base.convertkit": "n8n-nodes-base.convertKit",
    "n8n-nodes-base.convertkittrigger": "n8n-nodes-base.convertKitTrigger",

    # Copper
    "n8n-nodes-base.coppertrigger": "n8n-nodes-base.copperTrigger",

    # CrateDB
    "n8n-nodes-base.cratedb": "n8n-nodes-base.crateDb",

    # CrowdDev
    "n8n-nodes-base.crowddev": "n8n-nodes-base.crowdDev",
    "n8n-nodes-base.crowddevtrigger": "n8n-nodes-base.crowdDevTrigger",

    # CustomerIO
    "n8n-nodes-base.customerio": "n8n-nodes-base.customerIo",
    "n8n-nodes-base.customeriotrigger": "n8n-nodes-base.customerIoTrigger",

    # DeepL
    "n8n-nodes-base.deepl": "n8n-nodes-base.deepL",

    # DHL
    "n8n-nodes-base.dhl": "n8n-nodes-base.dhl",

    # E-goi
    "n8n-nodes-base.egoi": "n8n-nodes-base.eGoi",

    # Elasticsearch
    "n8n-nodes-base.elasticsearch": "n8n-nodes-base.elasticsearch",
    "n8n-nodes-base.elasticsecurity": "n8n-nodes-base.elasticSecurity",

    # ERPNext
    "n8n-nodes-base.erpnext": "n8n-nodes-base.erpNext",

    # Facebook
    "n8n-nodes-base.facebookgraphapi": "n8n-nodes-base.facebookGraphApi",
    "n8n-nodes-base.facebookleadadstrigger": "n8n-nodes-base.facebookLeadAdsTrigger",
    "n8n-nodes-base.facebooktrigger": "n8n-nodes-base.facebookTrigger",

    # FileMaker
    "n8n-nodes-base.filemaker": "n8n-nodes-base.fileMaker",

    # Figma
    "n8n-nodes-base.figmatrigger": "n8n-nodes-base.figmaTrigger",

    # Flow
    "n8n-nodes-base.flowtrigger": "n8n-nodes-base.flowTrigger",

    # FormIO
    "n8n-nodes-base.formiotrigger": "n8n-nodes-base.formIoTrigger",

    # Formstack
    "n8n-nodes-base.formstacktrigger": "n8n-nodes-base.formstackTrigger",

    # Freshdesk
    "n8n-nodes-base.freshdesk": "n8n-nodes-base.freshdesk",

    # Freshservice
    "n8n-nodes-base.freshservice": "n8n-nodes-base.freshservice",

    # Freshworks CRM
    "n8n-nodes-base.freshworkscrm": "n8n-nodes-base.freshworksCrm",

    # GetResponse
    "n8n-nodes-base.getresponse": "n8n-nodes-base.getResponse",
    "n8n-nodes-base.getresponsetrigger": "n8n-nodes-base.getResponseTrigger",

    # GitHub
    "n8n-nodes-base.github": "n8n-nodes-base.github",
    "n8n-nodes-base.githubtrigger": "n8n-nodes-base.githubTrigger",

    # GitLab
    "n8n-nodes-base.gitlab": "n8n-nodes-base.gitlab",
    "n8n-nodes-base.gitlabtrigger": "n8n-nodes-base.gitlabTrigger",

    # Gmail
    "n8n-nodes-base.gmailtrigger": "n8n-nodes-base.gmailTrigger",

    # Google
    "n8n-nodes-base.googleads": "n8n-nodes-base.googleAds",
    "n8n-nodes-base.googleanalytics": "n8n-nodes-base.googleAnalytics",
    "n8n-nodes-base.googlebigquery": "n8n-nodes-base.googleBigQuery",
    "n8n-nodes-base.googlebooks": "n8n-nodes-base.googleBooks",
    "n8n-nodes-base.googlebusinessprofile": "n8n-nodes-base.googleBusinessProfile",
    "n8n-nodes-base.googlebusinessprofiletrigger": "n8n-nodes-base.googleBusinessProfileTrigger",
    "n8n-nodes-base.googlecalendar": "n8n-nodes-base.googleCalendar",
    "n8n-nodes-base.googlecalendartrigger": "n8n-nodes-base.googleCalendarTrigger",
    "n8n-nodes-base.googlechat": "n8n-nodes-base.googleChat",
    "n8n-nodes-base.googlecloudfirestore": "n8n-nodes-base.googleCloudFirestore",
    "n8n-nodes-base.googlecloudnaturallanguage": "n8n-nodes-base.googleCloudNaturalLanguage",
    "n8n-nodes-base.googlecloudrealtimedatabase": "n8n-nodes-base.googleCloudRealtimeDatabase",
    "n8n-nodes-base.googlecloudstorage": "n8n-nodes-base.googleCloudStorage",
    "n8n-nodes-base.googlecontacts": "n8n-nodes-base.googleContacts",
    "n8n-nodes-base.googledocs": "n8n-nodes-base.googleDocs",
    "n8n-nodes-base.googledrive": "n8n-nodes-base.googleDrive",
    "n8n-nodes-base.googledrivetrigger": "n8n-nodes-base.googleDriveTrigger",
    "n8n-nodes-base.googleperspective": "n8n-nodes-base.googlePerspective",
    "n8n-nodes-base.googlesheets": "n8n-nodes-base.googleSheets",
    "n8n-nodes-base.googlesheetstrigger": "n8n-nodes-base.googleSheetsTrigger",
    "n8n-nodes-base.googleslides": "n8n-nodes-base.googleSlides",
    "n8n-nodes-base.googletasks": "n8n-nodes-base.googleTasks",
    "n8n-nodes-base.googletranslate": "n8n-nodes-base.googleTranslate",
    "n8n-nodes-base.gsuiteadmin": "n8n-nodes-base.gsuiteAdmin",
    "n8n-nodes-base.gotowebinar": "n8n-nodes-base.goToWebinar",

    # Gumroad
    "n8n-nodes-base.gumroadtrigger": "n8n-nodes-base.gumroadTrigger",

    # HackerNews
    "n8n-nodes-base.hackernews": "n8n-nodes-base.hackerNews",

    # HaloPSA
    "n8n-nodes-base.halopsa": "n8n-nodes-base.haloPsa",

    # HelpScout
    "n8n-nodes-base.helpscout": "n8n-nodes-base.helpScout",
    "n8n-nodes-base.helpscouttrigger": "n8n-nodes-base.helpScoutTrigger",

    # HighLevel
    "n8n-nodes-base.highlevel": "n8n-nodes-base.highLevel",

    # HomeAssistant
    "n8n-nodes-base.homeassistant": "n8n-nodes-base.homeAssistant",

    # HubSpot
    "n8n-nodes-base.hubspot": "n8n-nodes-base.hubspot",
    "n8n-nodes-base.hubspottrigger": "n8n-nodes-base.hubspotTrigger",

    # HumanticAI
    "n8n-nodes-base.humanticai": "n8n-nodes-base.humanticAi",

    # InvoiceNinja
    "n8n-nodes-base.invoiceninja": "n8n-nodes-base.invoiceNinja",
    "n8n-nodes-base.invoiceninjatrigger": "n8n-nodes-base.invoiceNinjaTrigger",

    # JinaAI
    "n8n-nodes-base.jinaai": "n8n-nodes-base.jinaAi",

    # Jira
    "n8n-nodes-base.jiratrigger": "n8n-nodes-base.jiraTrigger",

    # JotForm
    "n8n-nodes-base.jotformtrigger": "n8n-nodes-base.jotFormTrigger",

    # Kafka
    "n8n-nodes-base.kafkatrigger": "n8n-nodes-base.kafkaTrigger",

    # Keap
    "n8n-nodes-base.keaptrigger": "n8n-nodes-base.keapTrigger",

    # KoboToolbox
    "n8n-nodes-base.kobotoolbox": "n8n-nodes-base.koBoToolbox",
    "n8n-nodes-base.kobotoolboxtrigger": "n8n-nodes-base.koBoToolboxTrigger",

    # Lemlist
    "n8n-nodes-base.lemlisttrigger": "n8n-nodes-base.lemlistTrigger",

    # Linear
    "n8n-nodes-base.lineartrigger": "n8n-nodes-base.linearTrigger",

    # LinkedIn
    "n8n-nodes-base.linkedin": "n8n-nodes-base.linkedIn",

    # LoneScale
    "n8n-nodes-base.lonescale": "n8n-nodes-base.loneScale",
    "n8n-nodes-base.lonescaletrigger": "n8n-nodes-base.loneScaleTrigger",

    # Mailchimp
    "n8n-nodes-base.mailchimptrigger": "n8n-nodes-base.mailchimpTrigger",

    # MailerLite
    "n8n-nodes-base.mailerlite": "n8n-nodes-base.mailerLite",
    "n8n-nodes-base.mailerlitetrigger": "n8n-nodes-base.mailerLiteTrigger",

    # Mailjet
    "n8n-nodes-base.mailjettrigger": "n8n-nodes-base.mailjetTrigger",

    # Marketstack
    "n8n-nodes-base.marketstack": "n8n-nodes-base.marketstack",

    # Mattermost
    "n8n-nodes-base.mattermost": "n8n-nodes-base.mattermost",

    # Mautic
    "n8n-nodes-base.mautictrigger": "n8n-nodes-base.mauticTrigger",

    # MessageBird
    "n8n-nodes-base.messagebird": "n8n-nodes-base.messageBird",

    # Metabase
    "n8n-nodes-base.metabase": "n8n-nodes-base.metabase",

    # Microsoft
    "n8n-nodes-base.microsoftdynamicscrm": "n8n-nodes-base.microsoftDynamicsCrm",
    "n8n-nodes-base.microsoftentra": "n8n-nodes-base.microsoftEntra",
    "n8n-nodes-base.microsoftexcel": "n8n-nodes-base.microsoftExcel",
    "n8n-nodes-base.microsoftgraphsecurity": "n8n-nodes-base.microsoftGraphSecurity",
    "n8n-nodes-base.microsoftonedrive": "n8n-nodes-base.microsoftOneDrive",
    "n8n-nodes-base.microsoftonedrivetrigger": "n8n-nodes-base.microsoftOneDriveTrigger",
    "n8n-nodes-base.microsoftoutlook": "n8n-nodes-base.microsoftOutlook",
    "n8n-nodes-base.microsoftoutlooktrigger": "n8n-nodes-base.microsoftOutlookTrigger",
    "n8n-nodes-base.microsoftsharepoint": "n8n-nodes-base.microsoftSharePoint",
    "n8n-nodes-base.microsoftsql": "n8n-nodes-base.microsoftSql",
    "n8n-nodes-base.microsoftteams": "n8n-nodes-base.microsoftTeams",
    "n8n-nodes-base.microsoftteamstrigger": "n8n-nodes-base.microsoftTeamsTrigger",
    "n8n-nodes-base.microsofttodo": "n8n-nodes-base.microsoftToDo",

    # MISP
    "n8n-nodes-base.misp": "n8n-nodes-base.misp",

    # Mistral AI
    "n8n-nodes-base.mistralai": "n8n-nodes-base.mistralAi",

    # Monday.com
    "n8n-nodes-base.mondaycom": "n8n-nodes-base.mondayCom",

    # MongoDB
    "n8n-nodes-base.mongodb": "n8n-nodes-base.mongoDb",

    # Monica CRM
    "n8n-nodes-base.monicacrm": "n8n-nodes-base.monicaCrm",

    # MQTT
    "n8n-nodes-base.mqtt": "n8n-nodes-base.mqtt",
    "n8n-nodes-base.mqtttrigger": "n8n-nodes-base.mqttTrigger",

    # MySQL
    "n8n-nodes-base.mysql": "n8n-nodes-base.mySql",

    # NASA
    "n8n-nodes-base.nasa": "n8n-nodes-base.nasa",

    # Netscaler
    "n8n-nodes-base.netscaleradc": "n8n-nodes-base.netscalerAdc",

    # Netlify
    "n8n-nodes-base.netlifytrigger": "n8n-nodes-base.netlifyTrigger",

    # Nextcloud
    "n8n-nodes-base.nextcloud": "n8n-nodes-base.nextCloud",

    # NocoDB
    "n8n-nodes-base.nocodb": "n8n-nodes-base.nocoDb",

    # Notion
    "n8n-nodes-base.notiontrigger": "n8n-nodes-base.notionTrigger",

    # Odoo
    "n8n-nodes-base.odoo": "n8n-nodes-base.odoo",

    # Okta
    "n8n-nodes-base.okta": "n8n-nodes-base.okta",

    # OneSimpleAPI
    "n8n-nodes-base.onesimpleapi": "n8n-nodes-base.oneSimpleApi",

    # Onfleet
    "n8n-nodes-base.onfleettrigger": "n8n-nodes-base.onfleetTrigger",

    # OpenThesaurus
    "n8n-nodes-base.openthesaurus": "n8n-nodes-base.openThesaurus",

    # OpenWeatherMap
    "n8n-nodes-base.openweathermap": "n8n-nodes-base.openWeatherMap",

    # Oracle DB
    "n8n-nodes-base.oracledb": "n8n-nodes-base.oracleDb",

    # Oura
    "n8n-nodes-base.oura": "n8n-nodes-base.oura",

    # PagerDuty
    "n8n-nodes-base.pagerduty": "n8n-nodes-base.pagerDuty",

    # PayPal
    "n8n-nodes-base.paypal": "n8n-nodes-base.payPal",
    "n8n-nodes-base.paypaltrigger": "n8n-nodes-base.payPalTrigger",

    # Peekalink
    "n8n-nodes-base.peekalink": "n8n-nodes-base.peekalink",

    # PhantomBuster
    "n8n-nodes-base.phantombuster": "n8n-nodes-base.phantomBuster",

    # Philips Hue
    "n8n-nodes-base.philipshue": "n8n-nodes-base.philipsHue",

    # Pipedrive
    "n8n-nodes-base.pipedrivetrigger": "n8n-nodes-base.pipedriveTrigger",

    # Plivo
    "n8n-nodes-base.plivo": "n8n-nodes-base.plivo",

    # PostBin
    "n8n-nodes-base.postbin": "n8n-nodes-base.postBin",

    # Postgres
    "n8n-nodes-base.postgrestrigger": "n8n-nodes-base.postgresTrigger",

    # PostHog
    "n8n-nodes-base.posthog": "n8n-nodes-base.postHog",

    # Postmark
    "n8n-nodes-base.postmarktrigger": "n8n-nodes-base.postmarkTrigger",

    # ProfitWell
    "n8n-nodes-base.profitwell": "n8n-nodes-base.profitWell",

    # Pushbullet
    "n8n-nodes-base.pushbullet": "n8n-nodes-base.pushbullet",

    # Pushcut
    "n8n-nodes-base.pushcut": "n8n-nodes-base.pushcut",
    "n8n-nodes-base.pushcuttrigger": "n8n-nodes-base.pushcutTrigger",

    # Pushover
    "n8n-nodes-base.pushover": "n8n-nodes-base.pushover",

    # QuestDB
    "n8n-nodes-base.questdb": "n8n-nodes-base.questDb",

    # QuickBase
    "n8n-nodes-base.quickbase": "n8n-nodes-base.quickBase",

    # QuickBooks
    "n8n-nodes-base.quickbooks": "n8n-nodes-base.quickBooks",

    # QuickChart
    "n8n-nodes-base.quickchart": "n8n-nodes-base.quickChart",

    # RabbitMQ
    "n8n-nodes-base.rabbitmq": "n8n-nodes-base.rabbitMq",
    "n8n-nodes-base.rabbitmqtrigger": "n8n-nodes-base.rabbitMqTrigger",

    # Raindrop
    "n8n-nodes-base.raindrop": "n8n-nodes-base.raindrop",

    # Redis
    "n8n-nodes-base.redistrigger": "n8n-nodes-base.redisTrigger",

    # RocketChat
    "n8n-nodes-base.rocketchat": "n8n-nodes-base.rocketChat",

    # Rundeck
    "n8n-nodes-base.rundeck": "n8n-nodes-base.rundeck",

    # Salesforce
    "n8n-nodes-base.salesforcetrigger": "n8n-nodes-base.salesforceTrigger",

    # Salesmate
    "n8n-nodes-base.salesmate": "n8n-nodes-base.salesmate",

    # SeaTable
    "n8n-nodes-base.seatable": "n8n-nodes-base.seaTable",
    "n8n-nodes-base.seatabletrigger": "n8n-nodes-base.seaTableTrigger",

    # SecurityScorecard
    "n8n-nodes-base.securityscorecard": "n8n-nodes-base.securityScorecard",

    # SendGrid
    "n8n-nodes-base.sendgrid": "n8n-nodes-base.sendGrid",

    # Sendy
    "n8n-nodes-base.sendy": "n8n-nodes-base.sendy",

    # SentryIO
    "n8n-nodes-base.sentryio": "n8n-nodes-base.sentryIo",

    # ServiceNow
    "n8n-nodes-base.servicenow": "n8n-nodes-base.serviceNow",

    # SIGNL4
    "n8n-nodes-base.signl4": "n8n-nodes-base.signl4",

    # Shopify
    "n8n-nodes-base.shopifytrigger": "n8n-nodes-base.shopifyTrigger",

    # Slack
    "n8n-nodes-base.slacktrigger": "n8n-nodes-base.slackTrigger",

    # Snowflake
    "n8n-nodes-base.snowflake": "n8n-nodes-base.snowflake",

    # Splunk
    "n8n-nodes-base.splunk": "n8n-nodes-base.splunk",

    # Spotify
    "n8n-nodes-base.spotify": "n8n-nodes-base.spotify",

    # Stackby
    "n8n-nodes-base.stackby": "n8n-nodes-base.stackby",

    # Storyblok
    "n8n-nodes-base.storyblok": "n8n-nodes-base.storyblok",

    # Strapi
    "n8n-nodes-base.strapi": "n8n-nodes-base.strapi",

    # Strava
    "n8n-nodes-base.stravatrigger": "n8n-nodes-base.stravaTrigger",

    # Stripe
    "n8n-nodes-base.stripetrigger": "n8n-nodes-base.stripeTrigger",

    # Supabase
    "n8n-nodes-base.supabase": "n8n-nodes-base.supabase",

    # SurveyMonkey
    "n8n-nodes-base.surveymonkeytrigger": "n8n-nodes-base.surveyMonkeyTrigger",

    # SyncroMSP
    "n8n-nodes-base.syncromsp": "n8n-nodes-base.syncroMsp",

    # Taiga
    "n8n-nodes-base.taigatrigger": "n8n-nodes-base.taigaTrigger",

    # Tapfiliate
    "n8n-nodes-base.tapfiliate": "n8n-nodes-base.tapfiliate",

    # Telegram
    "n8n-nodes-base.telegramtrigger": "n8n-nodes-base.telegramTrigger",

    # TheHive
    "n8n-nodes-base.thehive": "n8n-nodes-base.theHive",
    "n8n-nodes-base.thehivetrigger": "n8n-nodes-base.theHiveTrigger",
    "n8n-nodes-base.thehive5": "n8n-nodes-base.theHive5",
    "n8n-nodes-base.thehive5trigger": "n8n-nodes-base.theHive5Trigger",

    # TimescaleDB
    "n8n-nodes-base.timescaledb": "n8n-nodes-base.timescaleDb",

    # Todoist
    "n8n-nodes-base.todoist": "n8n-nodes-base.todoist",

    # Toggl
    "n8n-nodes-base.toggltrigger": "n8n-nodes-base.togglTrigger",

    # TravisCI
    "n8n-nodes-base.travisci": "n8n-nodes-base.travisCi",

    # Trello
    "n8n-nodes-base.trellotrigger": "n8n-nodes-base.trelloTrigger",

    # Twake
    "n8n-nodes-base.twake": "n8n-nodes-base.twake",

    # Twilio
    "n8n-nodes-base.twiliotrigger": "n8n-nodes-base.twilioTrigger",

    # Twist
    "n8n-nodes-base.twist": "n8n-nodes-base.twist",

    # Typeform
    "n8n-nodes-base.typeformtrigger": "n8n-nodes-base.typeformTrigger",

    # UnleashedSoftware
    "n8n-nodes-base.unleashedsoftware": "n8n-nodes-base.unleashedSoftware",

    # UpLead
    "n8n-nodes-base.uplead": "n8n-nodes-base.upLead",

    # uProc
    "n8n-nodes-base.uproc": "n8n-nodes-base.uProc",

    # UptimeRobot
    "n8n-nodes-base.uptimerobot": "n8n-nodes-base.uptimeRobot",

    # urlscanio
    "n8n-nodes-base.urlscanio": "n8n-nodes-base.urlscanIo",

    # Venafi
    "n8n-nodes-base.venafitlsprotectcloud": "n8n-nodes-base.venafiTlsProtectCloud",
    "n8n-nodes-base.venafitlsprotectcloudtrigger": "n8n-nodes-base.venafiTlsProtectCloudTrigger",
    "n8n-nodes-base.venafitlsprotectdatacenter": "n8n-nodes-base.venafiTlsProtectDatacenter",

    # Vero
    "n8n-nodes-base.vero": "n8n-nodes-base.vero",

    # Vonage
    "n8n-nodes-base.vonage": "n8n-nodes-base.vonage",

    # Webflow
    "n8n-nodes-base.webflow": "n8n-nodes-base.webflow",
    "n8n-nodes-base.webflowtrigger": "n8n-nodes-base.webflowTrigger",

    # Wekan
    "n8n-nodes-base.wekan": "n8n-nodes-base.wekan",

    # WhatsApp
    "n8n-nodes-base.whatsapp": "n8n-nodes-base.whatsApp",
    "n8n-nodes-base.whatsapptrigger": "n8n-nodes-base.whatsAppTrigger",

    # Wise
    "n8n-nodes-base.wise": "n8n-nodes-base.wise",
    "n8n-nodes-base.wisetrigger": "n8n-nodes-base.wiseTrigger",

    # WooCommerce
    "n8n-nodes-base.woocommerce": "n8n-nodes-base.wooCommerce",
    "n8n-nodes-base.woocommercetrigger": "n8n-nodes-base.wooCommerceTrigger",

    # Workable
    "n8n-nodes-base.workabletrigger": "n8n-nodes-base.workableTrigger",

    # WordPress
    "n8n-nodes-base.wordpress": "n8n-nodes-base.wordPress",

    # Wufoo
    "n8n-nodes-base.wufootrigger": "n8n-nodes-base.wufooTrigger",

    # Xero
    "n8n-nodes-base.xero": "n8n-nodes-base.xero",

    # Yourls
    "n8n-nodes-base.yourls": "n8n-nodes-base.yourls",

    # YouTube
    "n8n-nodes-base.youtube": "n8n-nodes-base.youTube",

    # Zammad
    "n8n-nodes-base.zammad": "n8n-nodes-base.zammad",

    # Zendesk
    "n8n-nodes-base.zendesk": "n8n-nodes-base.zendesk",
    "n8n-nodes-base.zendesktrigger": "n8n-nodes-base.zendeskTrigger",

    # Zoho CRM
    "n8n-nodes-base.zohocrm": "n8n-nodes-base.zohoCrm",

    # Zoom
    "n8n-nodes-base.zoom": "n8n-nodes-base.zoom",

    # Zulip
    "n8n-nodes-base.zulip": "n8n-nodes-base.zulip",
}


def update_casing():
    """Aktualisiert alle Node-Types mit korrekter camelCase-Schreibweise"""
    conn = sqlite3.connect('n8n_docs.db')
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("Korrigiere Node-Type Groß-/Kleinschreibung")
    print("="*80 + "\n")

    updated = 0

    for lowercase_name, camelcase_name in CORRECT_CASING.items():
        try:
            # Aktualisiere in node_types_api
            cursor.execute('''
                UPDATE node_types_api
                SET node_type = ?
                WHERE LOWER(node_type) = LOWER(?)
            ''', (camelcase_name, lowercase_name))

            if cursor.rowcount > 0:
                updated += cursor.rowcount
                print(f"✓ {lowercase_name:45s} → {camelcase_name}")

        except sqlite3.Error as e:
            print(f"✗ Fehler bei {lowercase_name}: {e}")

    conn.commit()
    conn.close()

    print(f"\n{'='*80}")
    print(f"✅ {updated} Node-Types aktualisiert")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    update_casing()

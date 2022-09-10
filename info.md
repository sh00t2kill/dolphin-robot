# MyDolphin Plus

## Description

Integration with MyDolphin Plus. Creates the following components:

[Changelog](https://github.com/elad-bar/ha-mydholphin-plus/blob/master/CHANGELOG.md)

#### Requirements
- MyDolphin Plus App installed and configured

## How to

#### Installations via HACS
- In HACS, look for "MyDolphin Plus" and install
- In Configuration --> Integrations - Add MyDolphin Plus

#### Integration settings
###### Basic configuration (Configuration -> Integrations -> Add MyDolphin Plus)
| Fields name | Type    | Required | Default | Description                                   |
|-------------|---------|----------|---------|-----------------------------------------------|
| Username    | Textbox | -        |         | Username of dashboard user for MyDolphin Plus |
| Password    | Textbox | -        |         | Password of dashboard user for MyDolphin Plus |

###### Integration options (Configuration -> Integrations -> MyDolphin Plus Integration -> Options)
| Fields name | Type    | Required | Default              | Description                                   |
|-------------|---------|----------|----------------------|-----------------------------------------------|
| Username    | Textbox | -        | Last stored username | Username of dashboard user for MyDolphin Plus |
| Password    | Textbox | -        | Last stored password | Password of dashboard user for MyDolphin Plus |

###### Configuration validations
Upon submitting the form of creating an integration or updating options,

Component will try to log in into the MyDolphin Plus to verify new settings, following errors can appear:
- Integration already configured with the same title
- Invalid server details - Cannot reach the server

###### Encryption key got corrupted
If a persistent notification popped up with the following message:
```
Encryption key got corrupted, please remove the integration and re-add it
```

It means that encryption key was modified from outside the code,
Please remove the integration and re-add it to make it work again.

## Components

#### Binary Sensors

## Events


## Troubleshooting

Before opening an issue, please provide logs related to the issue,
For debug log level, please add the following to your config.yaml
```yaml
logger:
  default: warning
  logs:
    custom_components.mydolphin_plus: debug
```

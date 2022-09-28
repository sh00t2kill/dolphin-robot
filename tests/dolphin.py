######################################
## Example AppDaemon Configuration  ##
##                                  ##
## dolphin:                         ##
##   module: dolphin                ##
##   class: DolphinApp              ##
##   username: <username>           ##
##   password: <password>           ##
## The below are optional           ##
##   use_mqtt: True                 ##
##   mqtt_topic: dolphin            ##
##                                  ##
######################################


import datetime
import json

import appdaemon.plugins.hass.hassapi as hass

from robot import Dolphin


class DolphinApp(hass.Hass):

    logged_in = False
    username = ""
    password = ""
    topic = ""
    robot = False
    mqtt = False
    use_mqtt = False

    def initialize(self):
        self.log("Maytronics Dolphin App")

        self.username = self.args["username"]
        self.password = self.args["password"]

        self.log("Using username " + self.username)
        if "use_mqtt" in self.args:
            if self.args["use_mqtt"]:
                self.use_mqtt = True
                self.topic = self.args["mqtt_topic"]
                self.mqtt = self.get_plugin_api("MQTT")
                self.log("Publishing to MQTT Topic:" + self.topic)

        if not self.logged_in:
            self.log("Logging in to Maytronics API")
            self.robot = Dolphin()
            self.robot.login(self.username, self.password)
            self.logged_in = True
            self.log("Login Successful!")
        else:
            self.log("Logged in already, nothing to do")

        self.run_every(self.query_dolphin, "now", 60)

    def query_dolphin(self, c_time):

        try:
            items = self.robot.mapQuery()
        except BaseException:
            # If we have an exception, we probably got logged out. Lets log in again
            self.robot.login(self.username, self.password)
            items = self.robot.mapQuery()

        str_items = json.dumps(items)
        if self.use_mqtt:
            self.log("Publishing " + str_items + " to MQTT on topic " + self.topic)
            self.mqtt.mqtt_publish(topic=self.topic, payload=str_items, retain=True)
        items["friendly_name"] = "Dolphin " + self.robot.getSerial()
        if not self.use_mqtt:
            self.log("Updating sensor to " + str_items)
        self.set_state(
            "sensor.dolphin_last_run", state=items["last_run_status"], attributes=items
        )

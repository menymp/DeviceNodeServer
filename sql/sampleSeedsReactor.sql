-- 1) Create the script record (container runtime)
INSERT INTO scripts (name, entry_point, runtime, description, build_context, dockerfile, image_tag)
VALUES (
  'rfid-handler',
  'localhost:5000/local/rfid-worker:dev',
  'container',
  'RFID handler image that subscribes to RFID topics and routes open commands',
  'rfid',
  'Dockerfile',
  'localhost:5000/local/rfid-worker:dev'
);
SET @script_id = LAST_INSERT_ID();

-- 2) Create the script_instance that the reactor will spawn
INSERT INTO script_instances (script_id, instance_name, runtime, config_json, start_mode, enabled)
VALUES (
  @script_id,
  'rfid-instance-1',
  'container',
  '{
    "locks": [
      {
        "name": "front_door",
        "event_topic": "/NodeRfid1/rifd_sensor/value",
        "open_lock_topic": "/NodeRelays1/front_door_output/",
        "open_command": "OPEN"
      },
      {
        "name": "garage_door",
        "event_topic": "/NodeRfid3/rifd_sensor/value",
        "open_lock_topic": "/NodeRelays1/garage_door_output/",
        "open_command": "OPEN"
      }
    ],
    "restart_policy": {"max_restarts": 5, "backoff_seconds": 10}
  }',
  'always',
  1
);
SET @instance_id = LAST_INSERT_ID();


-- 1) Create the camera script record (container runtime)
INSERT INTO scripts (name, entry_point, runtime, description, build_context, dockerfile, image_tag)
VALUES (
  'camera-handler',
  'localhost:5000/local/camera-worker:dev',
  'container',
  'Camera motion detector that polls a JPEG URL, detects motion and emits MQTT events',
  'camera',
  'Dockerfile',
  'localhost:5000/local/camera-worker:dev'
);
SET @camera_script_id = LAST_INSERT_ID();

-- 2) Create the camera script_instance that the reactor will spawn
INSERT INTO script_instances (script_id, instance_name, runtime, config_json, start_mode, enabled)
VALUES (
  @camera_script_id,
  'camera-frontdoor-1',
  'container',
  '{
    "url":"http://192.168.1.16:8089/feed/mycapture.jpg",
    "mqtt_topic":"/cameras/frontdoor/motion",
    "sensitivity":30,
    "poll_interval":1.0,
    "last_event": null,
    "restart_policy": {"max_restarts": 5, "backoff_seconds": 10}
  }',
  'always',
  1
);
SET @camera_instance_id = LAST_INSERT_ID();

-- 3) Seed example user_rfids bindings (ensure user_id values exist in your users table)
INSERT INTO user_rfids (user_id, rfid_id, label, enabled)
VALUES
  (3, 'A1B2C3D4', 'personal tag', 1),
  (3, 'E5F6G7H8', 'Maintenance tag', 1);
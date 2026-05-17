-- scheduler_seeds.sql
INSERT INTO scheduler_rules (name, enabled, rule_json, safe_state) VALUES
(
  'Garden pump MWF Jan-Jun 1h',
  1,
  JSON_OBJECT(
    'type','timer',
    'scope','mqtt',
    'topic','/gardenNode/pump',
    'on_payload','ON',
    'off_payload','OFF',
    'weekdays', JSON_ARRAY('mon','wed','fri'),
    'months', JSON_ARRAY(1,2,3,4,5,6),
    'start_time','06:00:00',
    'duration_minutes', 60,
    'timezone','UTC'
  ),
  JSON_OBJECT('topic','/gardenNode/pump','payload','OFF')
);

INSERT INTO scheduler_rules (name, enabled, rule_json, safe_state) VALUES
(
  'Outside lights seasonal',
  1,
  JSON_OBJECT(
    'type','timer',
    'scope','mqtt',
    'topic','/lightsNode/outsideLights',
    'on_payload','ON',
    'off_payload','OFF',
    'seasonal', JSON_OBJECT(
      'jan_mar', JSON_OBJECT('start_time','19:30:00','end_time','07:00:00','months', JSON_ARRAY(1,2,3)),
      'apr_dec', JSON_OBJECT('start_time','20:00:00','end_time','06:00:00','months', JSON_ARRAY(4,5,6,7,8,9,10,11,12))
    ),
    'weekdays', JSON_ARRAY('mon','tue','wed','thu','fri','sat','sun'),
    'timezone','UTC'
  ),
  JSON_OBJECT('topic','/lightsNode/outsideLights','payload','OFF')
);

INSERT INTO scheduler_rules (name, enabled, rule_json, safe_state) VALUES
(
  'Coffee machine Mon-Fri 05:00-06:00',
  1,
  JSON_OBJECT(
    'type','timer',
    'scope','mqtt',
    'topic','/kitchen/coffeeMachine',
    'on_payload','ON',
    'off_payload','OFF',
    'weekdays', JSON_ARRAY('mon','tue','wed','thu','fri'),
    'start_time','05:00:00',
    'duration_minutes', 60,
    'timezone','UTC'
  ),
  JSON_OBJECT('topic','/kitchen/coffeeMachine','payload','OFF')
);

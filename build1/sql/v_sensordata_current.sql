-- View: v_sensordata_current

-- DROP VIEW v_sensordata_current;

CREATE OR REPLACE VIEW v_sensordata_current_2 AS 
 SELECT r1.id,
    r1.sensor_type,
    r1.data_read,
    to_timestamp(r1.time_read) AT TIME ZONE 'UTC' as time_read
   FROM ( SELECT row_number() OVER (PARTITION BY sensordata.sensor_type ORDER BY sensordata.time_read DESC) AS rn,
            sensordata.id,
            sensordata.sensor_type,
            sensordata.data_read,
            sensordata.time_read,
            sensordata.time_changed
           FROM sensordata) r1
  WHERE r1.rn = 1;

CREATE OR REPLACE VIEW v_sensordata_current AS 	
   SELECT r1.id,
    r1.sensor_type,
    r1.data_read,
    r1.time_read
   FROM ( SELECT row_number() OVER (PARTITION BY r0.sensor_type ORDER BY r0.date_added DESC,  r0.time_added DESC) AS rn,
            r0.id,
            r0.sensor_type,
            r0.data_read,
            (r0.date_added || ' ' || r0.time_added)::timestamp time_read
           FROM (
		select sc.*
		from sensordata sc
		where sc.date_added = now()::date
		order by sc.id desc
		limit 1000
           ) r0
         ) r1
  WHERE r1.rn = 1;
  
 
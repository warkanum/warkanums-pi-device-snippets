CREATE TABLE sensordata
(
  id bigserial NOT NULL,
  sensor_type text,
  data_read text,
  time_read bigint,
  time_changed bigint,
	date_added date,
	time_added time
  CONSTRAINT pk_id PRIMARY KEY (id),
  CONSTRAINT k_typeread UNIQUE (sensor_type, time_read)
)
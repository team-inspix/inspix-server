CREATE TABLE users (
	id integer,
	username text,
	face_image text,
	created_at datetime,
	password text
);

CREATE TABLE users_users (
	follow_from integer,
	follow_to integer
);

CREATE TABLE inspiration (
	id integer PRIMARY KEY AUTOINCREMENT,
	base_image_url text,
	backgroumd_image_url text,
	composited_image_url text,
	weather text,
	temperature text,
	captured_time datetime,
	longitude text,
	latitude text,
	caption text,
	created_at datetime,
	comment text,
	is_nokkari integer,
	author_id integer,
	nokkari_from integer
);


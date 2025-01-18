DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS HistData;




CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  Administrator BOOLEAN,
  cash FLOAT(2)
);

CREATE TABLE stock (
  record_id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT,
  name TEXT,
  actdate TEXT,
  currentprice FLOAT(4),
  user_id INTEGER NOT NULL,
  list_id INTEGER,
  buy BOOLEAN NOT NULL,
  act TEXT,
  share INTEGER NOT NULL,
  actprice FLOAT(4),
  added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user (id)
);


CREATE TABLE HistData (
  symbol VARCHAR(5),
  date DATE,
  close NUMERIC,
  PRIMARY KEY (symbol, date)
);
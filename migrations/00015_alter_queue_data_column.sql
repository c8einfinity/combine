# change the data column to mediumblob from blob, allow null
ALTER TABLE queue MODIFY data MEDIUMBLOB NULL;

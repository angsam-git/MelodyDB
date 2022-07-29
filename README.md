# MelodyDB

https://melodydb.herokuapp.com/

<img src = "melody.png" width = 700 > 


We implemented our database with real data from the Spotify API including artist, album and song information. Our application supports searching (artist, album and, song), commenting, and rating functions.

Ran with the command ```py server.py```

This repo contains mainly the front end. Queries are made on our PSQL database which has about a dozen tables and is filled with data from the Spotify API. The database was populated using another script https://github.com/angsam-git/populate_melody

Our artist page is for displaying artist information including artist name and artist album lists. For the album list, we need to pass in artist name so that we can find corresponding data in data table 'album' using data table 'artist 'and list out all the albums that are produced by that artist selected by the user. Our album page is for displaying album information including album title, album tracks and some other related information. For album tracks, we need to used the album title with data table 'song' to list all the songs in that album selected by user. These two pages are interesting because they do sql queries on multiple data tables and the for album page particular, it contains a commenting section that allow users to post comments. The comments will be added to our data table 'comment'.

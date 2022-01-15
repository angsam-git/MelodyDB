# MelodyDB

<img src = "melody.png" width = 700 > 



We implemented our datebase with real data from Spotify including artist, album and song information. Our application supports searching (artist, album and song), commenting, and modifying functions. We added a new feature that moderators can monitor and delete any comments while users can only delete their own comments. The only part that we did not implemented as we planned is the user preference function because we don't have any real user (only made up users for testing purpose ) right now and we want to finish the basic application before we start thinking about higher level functions. 

Our artist page is for displaying artist information including artist name and artist album lists. For the album list, we need to pass in artist name so that we can find corresponding data in data table 'album' using data table 'artist 'and list out all the albums that are produced by that artist selected by the user. Our album page is for displaying album information including album title, album tracks and some other related information. For album tracks, we need to used the album title with data table 'song' to list all the songs in that album selected by user. These two pages are interesting because they do sql query on multiple data tables and the for album page particular, it contains a commenting section that allow users to post comments. The comments will be added to our data table 'comment'.

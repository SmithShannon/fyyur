from app import db, Venue, Artist, Show, City, Genre, GenreVenue, GenreArtist

print(City.query.all())
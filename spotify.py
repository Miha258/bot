import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sys
import requests
from bs4 import BeautifulSoup
import requests



class ArtistNotFound(Exception): pass

class TrackNotFound(Exception): pass

class PlayListNotFound(Exception): pass

class AlbumNotFound(Exception): pass

def tracks(name:str):
   sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f"))
   results = sp.search(q=name,type='track')
   track_names = [ track['name'] for track in results['tracks']['items'] ]
   track_urls = [ track['external_urls']['spotify'] for track in results['tracks']['items'] ]
   autors = []
   for track in results['tracks']['items']:
     autors.append([artist['name'] for artist in track['artists']])
     
   return zip(track_names,track_urls,autors)

def albums(name:str):
   sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f"))
   results = sp.search(q=name,type='album')
   album_names = [ track['name'] for track in results['tracks']['items'] ]
   album_urls = [ track['external_urls']['spotify'] for track in results['tracks']['items'] ]
   autors = []
   for track in results['tracks']['items']:
     autors.append([artist['name'] for artist in track['artists']])
     
   return zip(album_urls,album_names,autors)

def artist(name:str):
  spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f"))
  if len(sys.argv) > 1:
    name = ' '.join(sys.argv[1:])
  
  
  results = spotify.search(q=name, type='artist')
  items = results['artists']['items']
  if len(items) > 0:
      artist = items[0]
      uri = items[0]['uri']
      results = spotify.artist_albums(uri, album_type='album')
      albums = results['items']
      while results['next']:
         results = spotify.next(results)
         albums.extend(results['items'])
  else:
    raise ArtistNotFound('Artsit not found')
      
      
  def get_auditions(id):
     r = requests.get(f'https://open.spotify.com/artist/{id}').content
     bs = BeautifulSoup(r,'html.parser')
     item  = bs.find('h3',class_ = "insights__column__number")
     return item.text.replace(',','')
  most_popular_tracks = [album['name'] for album in albums if album['name'] != None]
  track_urls = [ track['external_urls']['spotify'] for track in albums]
  
  return zip(most_popular_tracks,track_urls),artist['followers']['total'],artist['images'][0]['url'],artist['genres'],artist['external_urls']['spotify'],artist['name'],get_auditions(artist['id'])

def get_user_playlists(name:str):
     auth_manager = SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f")
     sp = spotipy.Spotify(auth_manager=auth_manager)
     if len(sys.argv) > 1:
       name = ' '.join(sys.argv[1:])
     result = sp.search(q=name, type='playlist')['playlists']['items']
     playlist_authors = [i['owner']['display_name'] for i in result]
     playlist_names = [i['name'] for i in result]
     playlist_url = [i['external_urls']['spotify'] for i in result]
     return zip(playlist_names,playlist_url,playlist_authors)



def get_track_info(url:str):
    try:
       spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f"))
       data = spotify.track(url)
       return data['duration_ms'],data['name'],[artist['name'] for artist in data['artists']],data['album']['name'],data['album']['images'][0]['url'],data['album']['external_urls']['spotify'],data['album']['release_date']
    except spotipy.SpotifyException:
       raise TrackNotFound('Track not found')

def get_playlist_info(url:str):
    try:
      spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f"))
      data = spotify.playlist(url)
      track_urls = [track['track']['external_urls']['spotify'] for track in data['tracks']['items']]
      track_names = [track['track']['name'] for track in data['tracks']['items']]
      return list(zip(track_urls,track_names)),data['name'],data['images'][0]['url']
    except spotipy.SpotifyException:
       raise PlayListNotFound('Playlist not found')

def get_album_info(url:str):
    try:
      spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f"))
      data = spotify.album(url)
      track_urls = [track['external_urls']['spotify'] for track in data['tracks']['items']]
      track_names = [track['name'] for track in data['tracks']['items']]
      return zip(track_urls,track_names),data['name'],data['artists'],data['name'],data['images'][0]['url'],[artist['name'] for artist in data['artists']]
    except spotipy.SpotifyException:
      raise AlbumNotFound('Album not found')

def get_artist_tracks(url:str):
    try:
      spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="bd96ff5a603140f38c0ee349fca6ff2f"))
      data = spotify.artist_top_tracks(url,'US')
      track_urls = [track['external_urls']['spotify'] for track in data['tracks']]
      return track_urls
    except spotipy.SpotifyException:
      raise ArtistNotFound('Artist musiclist not found')




import spotipy
import sys
import requests
from bs4 import BeautifulSoup
import requests


class ArtistNotFound(Exception): pass

class TrackNotFound(Exception): pass

class PlayListNotFound(Exception): pass

class AlbumNotFound(Exception): pass


def tracks(name:str):
   auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
   sp = spotipy.Spotify(auth=auth_token)
   results = sp.search(q=name,type='track',limit=5)
   track_names = [ track['name'] for track in results['tracks']['items'] ]
   track_urls = [ track['external_urls']['spotify'] for track in results['tracks']['items'] ]
   autors = []
   for track in results['tracks']['items']:
     autors.append([artist['name'] for artist in track['artists']])
     
   return zip(track_names,track_urls,autors)

def albums(name:str):
   auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
   sp = spotipy.Spotify(auth=auth_token)
   results = sp.search(q=name,type='album',limit=5)
   album_names = [ track['name'] for track in results['albums']['items'] ]
   album_urls = [ track['external_urls']['spotify'] for track in results['albums']['items'] ]
   autors = []
   for track in results['albums']['items']:
     autors.append([artist['name'] for artist in track['artists']])
     
   return zip(album_urls,album_names,autors)

def artist(name:str):
  auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
  spotify = spotipy.Spotify(auth=auth_token)
  if len(sys.argv) > 1:
    name = ' '.join(sys.argv[1:])

  results = spotify.search(q=name, type='artist',limit=5)
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
     auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
     sp = spotipy.Spotify(auth=auth_token)
     if len(sys.argv) > 1:
       name = ' '.join(sys.argv[1:])
     result = sp.search(q=name, type='playlist',limit=5)['playlists']['items']
     playlist_authors = [i['owner']['display_name'] for i in result]
     playlist_names = [i['name'] for i in result]
     playlist_url = [i['external_urls']['spotify'] for i in result]
     return zip(playlist_names,playlist_url,playlist_authors)


def get_track_info(url:str,outher_data = True):
    try:
        auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
        spotify = spotipy.Spotify(auth=auth_token)
        data = spotify.track(url)
        if outher_data:
          return data['duration_ms'],data['name'],[artist['name'] for artist in data['artists']],data['album']['name'],data['album']['images'][0]['url'],data['album']['external_urls']['spotify'],data['album']['release_date']
        else:
          return data['name'],[artist['name'] for artist in data['artists']],data['album']['images'][0]['url']
    except spotipy.SpotifyException:
       raise TrackNotFound('Track not found')


def get_playlist_info(url:str):
    try:
      auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
      spotify = spotipy.Spotify(auth=auth_token)
      data = spotify.playlist(url)
      track_urls = [track['track']['external_urls']['spotify'] for track in data['tracks']['items']]
      track_names = [track['track']['name'] for track in data['tracks']['items']]
      return list(zip(track_urls,track_names)),data['name'],data['images'][0]['url']
    except spotipy.SpotifyException:
       raise PlayListNotFound('Playlist not found')

def get_album_info(url:str):
    try:
      auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
      spotify = spotipy.Spotify(auth=auth_token)
      data = spotify.album(url)
      track_urls = [track['external_urls']['spotify'] for track in data['tracks']['items']]
      track_names = [track['name'] for track in data['tracks']['items']]
      return zip(track_urls,track_names),data['name'],data['artists'],data['name'],data['images'][0]['url'],[artist['name'] for artist in data['artists']]
    except spotipy.SpotifyException:
      raise AlbumNotFound('Album not found')


def get_artist_tracks(url:str,region:str):
    try:
      auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
      spotify = spotipy.Spotify(auth=auth_token)
      data = spotify.artist_top_tracks(url,str(region)[:2].upper())
      track_urls = [track['external_urls']['spotify'] for track in data['tracks']]
      return track_urls
    except spotipy.SpotifyException:
      raise ArtistNotFound('Artist musiclist not found')

def search(query:str):
      auth_token = spotipy.oauth2.SpotifyClientCredentials(client_id="a1bba52790704d4d8d1c5ece8ea930a5",client_secret="cabaaf0e038641969ef32f2489d7d6c8").get_access_token(False)
      spotify = spotipy.Spotify(auth=auth_token)
      result = spotify.search(query,limit=1)
      return result['tracks']['items'][0]['external_urls']['spotify'] if result['tracks']['items'] else None
      


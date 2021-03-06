from flask import Flask, request
import flask
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
from scipy.spatial.distance import pdist, squareform

app = Flask(__name__)

def auth():
    token = request.args.get('token')
    #scope = 'user-top-read'
    global sp
    sp = spotipy.Spotify(auth=token)

def getUserProfile(top_tracks):
    track_ids = [top_tracks['items'][i]['id'] for i in range(len(top_tracks['items']))]
    features = sp.audio_features(track_ids)
    ftrs = pd.DataFrame(features)
    return ftrs.describe().loc['mean']

def getRelatedArtistsUris(top_artists):
    for i in range(len(top_artists['items'])):
        uri = top_artists['items'][i]['uri']
        related_artists = sp.artist_related_artists(uri)
        related_artists_uris = [related_artists['artists'][i]['uri'] for i in range(len(related_artists['artists']))]
    return related_artists_uris

def getRelatedTracks(uris):
    related_tracks = []
    for uri in uris:
        artist_top_tracks = sp.artist_top_tracks(uri)
        related_tracks.append(artist_top_tracks)
    return related_tracks

def getRelatedTracksIds(related_tracks):
    ids = []
    for i in range(len(related_tracks)):
        ids.append([related_tracks[i]['tracks'][j]['id'] for j in range(len(related_tracks[i]['tracks']))])
    return ids

def getRelatedFeaturesDataFrame(related_tracks_ids):
    df = pd.DataFrame(related_tracks_ids)
    ids = df.values.flatten()
    features_batch_1 = sp.audio_features(ids[:100])
    features_batch_2 = sp.audio_features(ids[100:])
    features_batch_1
    batch_1 = pd.DataFrame(features_batch_1)
    batch_2 = pd.DataFrame(features_batch_2)
    df = pd.concat([batch_1, batch_2])
    df.set_index('id', inplace=True)
    df.drop(['type', 'uri', 'track_href', 'analysis_url'], axis=1, inplace=True)
    return df

def getSimilitudDataFrame(df, user_profile):
    df.loc['User']=user_profile
    df.index
    distancias=squareform(pdist(df, 'euclidean'))
    similitud=pd.DataFrame(1/(1+distancias), index=df.index, columns=df.index)
    return similitud

def getRecommendations(similitud):
    return similitud.User.sort_values(ascending=False)[1:51].index

@app.route('/profile')
def recommendByProfile():
    auth()

    top_artists = sp.current_user_top_artists(time_range='long_term', limit=50)
    top_tracks = sp.current_user_top_tracks(time_range='long_term', limit=50)

    user_profile = getUserProfile(top_tracks)
    artists_uris = getRelatedArtistsUris(top_artists)
    related_tracks = getRelatedTracks(artists_uris)
    related_tracks_ids = getRelatedTracksIds(related_tracks)
    df = getRelatedFeaturesDataFrame(related_tracks_ids)
    similitud = getSimilitudDataFrame(df, user_profile)
    recomended_ids = getRecommendations(similitud)

    return flask.jsonify(ids=list(recomended_ids))

def getMoodProfile(track_ids):
    features = sp.audio_features(track_ids)
    ftrs = pd.DataFrame(features)
    return ftrs.describe().loc['mean']

def getRelatedMoodArtistsUris(ids):
    results = sp.tracks(ids)
    return [track['artists'][0]['uri'] for track in results['tracks']]

@app.route('/mood')
def recommendByMood():
    auth()

    id1 = request.args.get('id1')
    id2 = request.args.get('id2')
    id3 = request.args.get('id3')
    id4 = request.args.get('id4')
    id5 = request.args.get('id5')
    ids = [id1, id2, id3, id4, id5]

    mood_profile = getMoodProfile(ids)
    related_artists_uris = getRelatedMoodArtistsUris(ids)
    related_tracks = getRelatedTracks(related_artists_uris)
    related_tracks_ids = getRelatedTracksIds(related_tracks)
    df = getRelatedFeaturesDataFrame(related_tracks_ids)
    similitud = getSimilitudDataFrame(df, mood_profile)
    recomended_ids = getRecommendations(similitud)


    return flask.jsonify(ids=list(recomended_ids))

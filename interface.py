import PySimpleGUI as sg
import pandas as pd
import matplotlib.pyplot as plt
from textblob import TextBlob
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from bs4 import BeautifulSoup


def get_twitter_comments(tweet_url):
    comments = []
    response = requests.get(tweet_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        comment_elements = soup.find_all('div', {'class': 'css-901oao'})
        for element in comment_elements:
            comment_text = element.find('span').text
            comments.append(comment_text)
    return comments


def get_video_comments(video_id):
    api_key = 'AIzaSyBgMVoXZsDNQcBaAOExgGDvaB7EOeeYplo'

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        comments = []
        next_page_token = ''

        while True:
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                textFormat='plainText',
                pageToken=next_page_token
            ).execute()

            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)

            if 'nextPageToken' in response:
                next_page_token = response['nextPageToken']
            else:
                break

        return comments

    except HttpError as e:
        print('Une erreur HTTP est survenue:')
        print(e)

    except Exception as e:
        print('Une erreur est survenue:')
        print(e)

def get_facebook_comments(post_id, access_token):
    base_url = f'https://graph.facebook.com/v12.0/{post_id}/comments'
    params = {
        'access_token': access_token,
        'limit': 100
    }

    comments = []
    next_page = True
    while next_page:
        response = requests.get(base_url, params=params)
        data = response.json()
        if 'data' in data:
            comments += [comment['message'] for comment in data['data']]

        if 'paging' in data and 'next' in data['paging']:
            next_page_url = data['paging']['next']
            params = None
            next_page = True
        else:
            next_page = False

    return comments

def get_face_comments(face_id):
    post_id = 'POST_ID'
    access_token = 'VOTRE_ACCESS_TOKEN'
    comments = get_facebook_comments(post_id, access_token)
    for comment in comments:
        print(comment)

def analyze_sentiments(link):
    if link:
        if values['-YOUTUBE-']:
            video_id = link.split('=')[1]
            comments = get_video_comments(video_id)
        elif values['-TWITTER-']:
            tweet_id = link.split('/')[-1]
            comments = get_twitter_comments(tweet_id)
        elif values['-FACEBOOK-']:
            comments = get_face_comments(face_id)

        sentiment_scores = []
        for comment in comments:
            blob = TextBlob(comment)
            sentiment_score = blob.sentiment.polarity
            sentiment_scores.append(sentiment_score)

        sentiments = ['positive' if score > 0 else 'negative' if score < 0 else 'neutral' for score in sentiment_scores]
        data = pd.DataFrame({'comment': comments, 'sentiment': sentiments})
        data.to_csv('resultats.csv', index=False)
        percentage_positive = round((data['sentiment'] == 'positive').mean() * 100, 2)
        percentage_negative = round((data['sentiment'] == 'negative').mean() * 100, 2)
        percentage_neutral = round((data['sentiment'] == 'neutral').mean() * 100, 2)
        return percentage_positive, percentage_negative, percentage_neutral
    else:
        return 0, 0, 0


def visualize_results():
    data = pd.read_csv('resultats.csv')
    percentages = [round((data['sentiment'] == 'positive').mean() * 100, 2),
                   round((data['sentiment'] == 'negative').mean() * 100, 2),
                   round((data['sentiment'] == 'neutral').mean() * 100, 2)]
    labels = ['Positive', 'Negative', 'Neutral']
    plt.bar(labels, percentages)
    for i, v in enumerate(percentages):
        plt.text(i, v + 1, str(v) + '%', ha='center', va='bottom')
    plt.title('Analyse des sentiments')
    plt.xlabel('Sentiments')
    plt.ylabel('Pourcentage')
    plt.savefig('resultats.jpg', format='jpeg')


layout = [
    [sg.Text('Choisissez la plateforme :'), sg.Radio('YouTube', 'PLATEFORME', key='-YOUTUBE-', default=True),
     sg.Radio('Twitter', 'PLATEFORME', key='-TWITTER-'), sg.Radio('Facebook', 'PLATEFORME', key='-FACEBOOK-')],
    [sg.Text('Entrez le lien de la vidéo :')],
    [sg.Input(key='-LINK-')],
    [sg.Button('Analyser'), sg.Button('Visualiser les résultats'), sg.Button('Télécharger résultats CSV'),
     sg.Button('Télécharger résultats graphique'), sg.Button('Quitter')],
    [sg.Text('')],
    [sg.Text('Résultats :', key='-RESULTS-', size=(80, 3), justification='left')]
]

window = sg.Window('Analyse des Sentiments', layout, size=(600, 200))

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED or event == 'Quitter':
        break
    elif event == 'Analyser':
        link = values['-LINK-']
        positive, negative, neutral = analyze_sentiments(link)
        results_text = f"Pourcentage de commentaires positifs : {positive}%\n" \
                       f"Pourcentage de commentaires négatifs : {negative}%\n" \
                       f"Pourcentage de commentaires neutres : {neutral}%"
        window['-RESULTS-'].update(results_text)
    elif event == 'Visualiser les résultats':
        data = pd.read_csv('resultats.csv')
        sg.Print(data)
    elif event == 'Télécharger résultats CSV':
        data = pd.read_csv('resultats.csv')
        data.to_csv('resultats.csv', index=False)
        sg.popup('Fichier CSV téléchargé avec succès !', title='Téléchargement')
    elif event == 'Télécharger résultats graphique':
        visualize_results()
        sg.popup('Graphique des résultats téléchargé avec succès !', title='Téléchargement')

window.close()

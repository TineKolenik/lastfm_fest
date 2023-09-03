import requests, json, streamlit as st, io
from PIL import Image, ImageDraw, ImageFont
import os

api_key = st.secrets["LASTFM_API_KEY"]

st.set_page_config(layout="wide")


def fetch_top_artists(api_key, username, period, limit):
    period_map = {'6 months': '6month', '1 year': '12month', 'all time': 'overall'}
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={username}&api_key={api_key}&format=json&period={period_map[period]}&limit={limit}"
    response = requests.get(url)
    data = json.loads(response.text)
    return [artist['name'] for artist in data['topartists']['artist']] if response.status_code == 200 else None


def generate_poster(top_artists, background_style, festival_name):
    if top_artists is None:
        return None

    img = Image.open(f"{background_style.lower()}_background.png")
    d = ImageDraw.Draw(img)
    fest_fnt = ImageFont.truetype("Tisa Sans Pro ExtraBold Italic.ttf", 130)
    day_fnt = ImageFont.truetype("Tisa Sans Pro Bold.ttf", 30)
    fnt = ImageFont.truetype("Populaire.ttf", 110)
    small_fnt = ImageFont.truetype("Populaire.ttf", 70)
    smaller_fnt = ImageFont.truetype("Populaire.ttf", 50)

    max_line_width = (img.width * 2) // 3  # Define max_line_width here

    # Center the festival name at the top of the image
    fest_text_width, fest_text_height = d.textsize(festival_name, font=fest_fnt)
    fest_x_position = (img.width - fest_text_width) // 2
    d.text((fest_x_position, 80), festival_name, font=fest_fnt, fill=(255, 255, 255))

    # Initialize variables
    y_position = fest_text_height + 250  # Start below the festival name
    gap = 20

    # Divide artists into headliners, medium, and small categories
    headliners = top_artists[:3] if len(top_artists) >= 3 else top_artists
    medium_artists = top_artists[3:12] if len(top_artists) >= 12 else top_artists[3:]
    small_artists = top_artists[12:27] if len(top_artists) >= 27 else []

    for headliner, medium, small in zip(
            headliners,
            [medium_artists[i:i + 3] for i in range(0, len(medium_artists), 3)],
            [small_artists[i:i + 5] for i in range(0, len(small_artists), 5)]
    ):

        # Draw headliner name in center
        max_headliner_width = 600  # or any other value you choose

        text_width, text_height = d.textsize(headliner, font=fnt)

        if text_width > max_headliner_width:
            # Break the headliner name into two lines
            mid_point = len(headliner) // 2  # Find the middle point of the string
            split_point = headliner.rfind(' ', 0, mid_point)  # Find the nearest space to the middle point
            line1 = headliner[:split_point]  # First line
            line2 = headliner[split_point + 1:]  # Second line

            # Draw first line
            text_width1, text_height1 = d.textsize(line1, font=fnt)
            x_position1 = (img.width - text_width1) // 2
            d.text((x_position1, y_position), line1, font=fnt, fill=(255, 255, 255))

            # Update y_position for the second line
            y_position += text_height1 + gap

            # Draw second line
            text_width2, text_height2 = d.textsize(line2, font=fnt)
            x_position2 = (img.width - text_width2) // 2
            d.text((x_position2, y_position), line2, font=fnt, fill=(255, 255, 255))

            # Update y_position for the next artist group
            y_position += text_height2

        else:
            x_position = (img.width - text_width) // 2
            d.text((x_position, y_position), headliner, font=fnt, fill=(255, 255, 255))

            # Update y_position for the next artist group
            y_position += text_height

        y_position += gap  # Add gap after headliner for next artist group

        # Draw day of the week on the extreme left
        day_of_week = ["Saturday", "Sunday", "Monday"][headliners.index(headliner)]
        day_text_width, day_text_height = d.textsize(day_of_week, font=day_fnt)
        d.text((250, y_position - 60), day_of_week, font=day_fnt, fill=(204,204,0))

        # Draw date on the extreme right
        date = ["Jun 1", "Jun 2", "Jun 3"][headliners.index(headliner)]
        date_text_width, date_text_height = d.textsize(date, font=day_fnt)
        d.text((img.width - date_text_width - 250, y_position - 60), date, font=day_fnt, fill=(204,204,0))

#        y_position += text_height + gap

        def handle_artists(artists, font):
            nonlocal y_position
            split_sym = ' • '
            artist_text = split_sym.join(artists)
            lines = []
            line = []
            for word in artist_text.split(split_sym):
                if d.textsize(split_sym.join(line + [word]), font=font)[0] <= max_line_width:
                    line.append(word)
                else:
                    lines.append(split_sym.join(line))
                    line = [word]
            lines.append(split_sym.join(line))
            for line in lines:
                text_width, text_height = d.textsize(line, font=font)
                x_position = (img.width - text_width) // 2
                d.text((x_position, y_position), line, font=font, fill=(255, 255, 255))
                y_position += text_height + gap

            # Add a gap after the smallest artists
            if font == smaller_fnt:
                y_position += 80  # adjust this number as needed

        handle_artists(medium, small_fnt)
        handle_artists(small, smaller_fnt)

    return img

st.title('Festival Poster Generator')
if 'page' not in st.session_state: st.session_state.page = 1
if 'username' not in st.session_state: st.session_state.username = ''
if st.session_state.page == 1:
    st.session_state.username = st.text_input('Enter your Last.fm username:')
    if st.button('Continue'):
        st.session_state.page = 2

elif st.session_state.page == 2:
    st.header('Customize')
    col1, col2 = st.columns([1, 1])
    with col2:
        st.subheader('Customize')
        time_frame = st.selectbox('Timeframe to take top artists from:', ['6 months', '1 year', 'all time'], key="time_frame")
        background_style = st.selectbox('Choose the style of the background image:', ['Summer', 'Winter', 'Space'], key="background_style")
        festival_name = st.text_input('Name of your festival:', st.session_state.username + 'Fest')
        top_artists = fetch_top_artists(api_key, st.session_state.username, st.session_state.get("time_frame", "1 week"), 27)
        img = generate_poster(top_artists, st.session_state.get("background_style", "Summer"), st.session_state.get("festival_name", st.session_state.username + 'Fest'))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        st.download_button("Download Poster", data=buffered.getvalue(), file_name=f"{festival_name}.png", mime="image/png")

        # Add a "Go back to try another user" button here
        if st.button('Go back to try another user'):
            st.session_state.page = 1
    with col1:
        st.subheader('Preview')
        img = generate_poster(top_artists, st.session_state.get("background_style", "Summer"), st.session_state.get("festival_name", st.session_state.username + 'Fest'))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        st.image(buffered.getvalue(), caption='Your Festival Poster', use_column_width=True)



"""Dancing with SARs — NASA Space Apps 2026 education/research prototype.
Run: streamlit run app.py
All guided 'before/after' examples are simulated, not NISAR data.
"""
from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
import json
import textwrap
from urllib.parse import urlencode
import requests
import streamlit as st
import pandas as pd
import numpy as np

from sar_engine import (
    LOCATIONS, CHANGES, make_demo, sar_gray, change_heatmap, img_bytes,
    analyze_aligned_csv, matrix_from_csv, demo_csv, align_visual_pair,
)

BASE = Path(__file__).resolve().parent
NASA_LINKS = {
    'NASA NISAR Mission': 'https://science.nasa.gov/mission/nisar/',
    'NISAR Data Overview': 'https://science.nasa.gov/mission/nisar/data/',
    'ASF Vertex Search (real NISAR data)': 'https://search.asf.alaska.edu/',
    'NISAR Data Access Guide': 'https://nisar-docs.asf.alaska.edu/access-overview/',
    'NASA Earthdata Search': 'https://search.earthdata.nasa.gov/',
    'ISRO Bhoonidhi': 'https://bhoonidhi.nrsc.gov.in/',
    'Official Dancing with the SARs Challenge': 'https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/',
}

st.set_page_config(page_title='Dancing with SARs | NISAR Explorer', page_icon='🛰️', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''
<style>
html,body,[data-testid="stAppViewContainer"],.stApp {background:#f4f8fa !important;color:#142a3d!important;}
[data-testid="stHeader"] {background:rgba(244,248,250,.92)!important;}
[data-testid="stSidebar"] {background:#e7f1f3!important;}
[data-testid="stAppViewBlockContainer"] {padding-top:1.5rem;max-width:1300px;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,span,label {color:#142a3d;}
[data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2,[data-testid="stMarkdownContainer"] h3 {color:#122e47;}
.stButton>button[kind="primary"] {background:#086c72!important;color:#fff!important;border-radius:12px!important;font-weight:700!important;border:0!important;}
.stButton>button {border-radius:12px!important;font-weight:650!important;}
[data-testid="stMetric"] {background:#fff;padding:14px;border-radius:15px;border:1px solid #d7e8ed;}
[data-testid="stMetricValue"] {color:#083f56!important;}
[data-testid="stTabs"] button {color:#193c54!important;font-weight:650;}
[data-testid="stTabs"] button[aria-selected="true"] {color:#08767b!important;}
[data-testid="stExpander"] {background:#fff;border:1px solid #d7e8ed;border-radius:12px;}
[data-testid="stAlert"] {color:#163749;}
.pill {display:inline-block;background:#d8f4ec;border:1px solid #b6e6db;color:#115b57!important;padding:5px 12px;border-radius:22px;font-weight:700;font-size:.8rem;}
.notice {padding:13px 16px;background:#fff6e3;border-left:5px solid #e7a63e;border-radius:10px;color:#5c4426!important;}
.info-card {border:1px solid #d4e4eb;background:#fff;border-radius:15px;padding:18px;min-height:155px;}
.small-label {font-weight:750;color:#13777c!important;letter-spacing:.07em;font-size:.8rem;}
.fine {font-size:.83rem;color:#586a7c!important;}
hr {border-color:#e1eaed!important;}
@media(max-width:768px){[data-testid="stAppViewBlockContainer"]{padding:1rem .75rem 3rem!important}.info-card{min-height:unset;padding:13px}.stTabs button{font-size:.75rem!important;padding:.4rem .25rem!important}}
</style>
''', unsafe_allow_html=True)

for key, initial in {'reports': [], 'quiz_score': None, 'upload_mode':'Guided simulation'}.items():
    if key not in st.session_state: st.session_state[key] = initial

st.image(str(BASE/'assets'/'radar_hero.svg'), use_container_width=True)
st.markdown('<span class="pill">NASA × ISRO NISAR  •  Research & learning prototype</span>', unsafe_allow_html=True)
st.caption('Choose a place and surface-change topic, examine a teaching example, or bring your own aligned radar measurements for analysis.')

# Top bar with reassuring provenance status
k1,k2,k3 = st.columns(3)
with k1: st.metric('Investigation areas', f'{len(LOCATIONS)} + custom')
with k2: st.metric('Surface-change topics', len(CHANGES))
with k3: st.metric('Saved observations', len(st.session_state.reports))

explore, compare, learn, notebook, resources = st.tabs([
    '🌍 Explore Earth', '📡 Compare data', '🧠 Radar learning', '📝 Research notebook', '🔗 NASA resources'
])

with explore:
    st.subheader('Choose your investigation')
    c1,c2 = st.columns(2)
    with c1:
        place = st.selectbox('Where would you like to investigate?', list(LOCATIONS)+['Custom coordinates'], index=0)
        if place=='Custom coordinates':
            lat=st.number_input('Latitude', -90.0, 90.0, 24.46, format='%.4f', key='lat')
            lon=st.number_input('Longitude', -180.0, 180.0, 54.37, format='%.4f', key='lon')
            place_display=f'Custom location ({lat:.3f}, {lon:.3f})'
        else:
            lat,lon,_=LOCATIONS[place];place_display=place
    with c2:
        kind=st.selectbox('What kind of change interests you?', list(CHANGES), index=0)
        st.caption(CHANGES[kind]['hint'])
    c3,c4 = st.columns(2)
    with c3:
        earlier=st.date_input('Observation A (before)', value=date(2026,7,1), min_value=date(2025,7,30), max_value=date.today(), key='earlier')
    with c4:
        later=st.date_input('Observation B (after)', value=min(date.today(),date(2026,10,15)), min_value=date(2025,7,30), max_value=date.today(), key='later')
    if earlier>=later:
        st.error('Choose an after-date later than the before-date.')
        day_gap=1
    else:day_gap=(later-earlier).days
    st.markdown('**Selected location**')
    st.map(pd.DataFrame({'lat':[lat], 'lon':[lon]}), zoom=4, height=260)
    st.markdown('<div class="notice"><strong>Guided simulation — NOT actual NISAR observations.</strong> The maps below are generated illustrations. The selected dates only adjust the fictional change pattern; they do not query a satellite archive.</div>', unsafe_allow_html=True)
    before,after=make_demo(place_display,kind,day_gap)
    ab,aa=st.columns(2)
    with ab:
        st.markdown(f'**Before · {earlier.isoformat()}**')
        st.image(sar_gray(before), use_container_width=True)
    with aa:
        st.markdown(f'**After · {later.isoformat()}**')
        st.image(sar_gray(after), use_container_width=True)
    th=st.slider('Visual change highlight (illustrative dB difference)',1.,8.,3.,.5)
    d1,d2=st.columns([2,1])
    with d1:
        st.markdown('**Difference preview (simulated)**')
        st.image(change_heatmap(before,after,th),use_container_width=True)
        st.caption('Teal = stronger simulated radar response; orange = weaker simulated response; dark blue = little difference.')
    with d2:
        diff=after-before
        st.metric('Example mean change',f'{diff.mean():+.2f} dB')
        st.metric('Highlighted example pixels',f'{(np.abs(diff)>=th).mean()*100:.1f}%')
        st.caption('Illustrative values only. No satellite data were fetched for this estimate.')
        st.download_button('⬇️ Save demo comparison',img_bytes(change_heatmap(before,after,th)),file_name='simulated_change.png',mime='image/png', use_container_width=True)
    st.info(CHANGES[kind]['reality'])
    with st.expander('Scientific question for students'):
        st.write(CHANGES[kind]['question'])
        st.write('Find two *real* NISAR observations for the same place with compatible orbit geometry, acquisition mode and calibration. Then compare them using the appropriate processing method.')
        st.link_button('Find real observations in ASF Vertex',NASA_LINKS['ASF Vertex Search (real NISAR data)'])
    with st.expander('🔎 Search the LIVE ASF NISAR acquisition catalog'):
        st.write('Search the real NASA/ASF acquisition catalog near your selected coordinates. This retrieves scene metadata only; it does not download or automatically compare radar data.')
        if st.button('Search real NISAR scenes',type='primary'):
            if earlier >= later:
                st.error('Please choose two valid dates in order to search.')
            else:
                params={'dataset':'NISAR','processingLevel':'GCOV','intersectsWith':f'POINT({lon:.4f} {lat:.4f})','start':str(earlier),'end':str(later),'output':'geojson','maxResults':10}
                endpoint='https://api.daac.asf.alaska.edu/services/search/param'
                with st.spinner('Searching the ASF catalog...'):
                    try:
                        response=requests.get(endpoint,params=params,timeout=12,headers={'Accept':'application/geo+json'})
                        response.raise_for_status()
                        payload=response.json()
                        if not isinstance(payload,dict) or 'features' not in payload:raise ValueError('Unexpected catalog response')
                        st.session_state['asf_search']={'rows':[(f.get('properties') or {}) for f in payload.get('features',[])[:10]],'url':response.url}
                    except Exception as exc:
                        st.session_state['asf_search']=None
                        st.warning(f'ASF catalog could not be reached or returned an error: {exc}. Try the Vertex search link instead.')
        real_result=st.session_state.get('asf_search')
        if real_result is not None:
            rows=real_result['rows']
            st.write(f'**{len(rows)} records displayed** (up to 10; catalog may have more).')
            if rows:
                cleaned=[]
                for r in rows:
                    cleaned.append({'Scene / granule':r.get('sceneName') or r.get('fileName') or r.get('fileID') or 'No ID', 'Acquired':r.get('startTime') or r.get('start') or '', 'Product':r.get('processingLevel') or '', 'Orbit':r.get('flightDirection') or ''})
                st.dataframe(pd.DataFrame(cleaned),hide_index=True,use_container_width=True)
                st.download_button('⬇️ Export scene metadata',pd.DataFrame(cleaned).to_csv(index=False).encode(),'asf_nisar_search_results.csv','text/csv')
            else:
                st.info('No GCOV acquisitions matched this point and date range in the API response. Try a longer interval or another location in Vertex.')
            st.link_button('Open this query on ASF Search API', real_result['url'])
            st.caption('Only results retrieved from the live ASF service count as verified catalog records. Search results are not evidence that a physical change occurred.')
    st.session_state['active_scenario']={'place':place_display,'lat':lat,'lon':lon,'kind':kind,'earlier':str(earlier),'later':str(later),'provenance':'SIMULATED DEMO'}

with compare:
    st.subheader('Compare your own observations')
    st.caption('Two analysis paths are available. Data do not upload to NASA automatically; files are processed in this Streamlit session.')
    upload_mode=st.radio('Comparison method', ['Numeric backscatter grid (CSV)', 'Visual images (PNG/JPG)'], horizontal=True)
    if upload_mode=='Numeric backscatter grid (CSV)':
        st.markdown('**For processed, co-registered radar backscatter in dB.**')
        st.write('Required columns: `row`, `col`, `before_db`, `after_db`. Each row represents one matching grid cell. The app calculates after − before in dB and a threshold-based flag.')
        st.download_button('⬇️ Download example CSV (SIMULATED)',demo_csv(),'simulated_grid_example.csv','text/csv')
        csv_upload=st.file_uploader('Upload a CSV exported from your radar-processing workflow',type=['csv'],key='csv')
        threshold=st.slider('Highlight |Δ backscatter| of at least (dB)',1.0,10.0,3.0,0.5,key='csvthreshold')
        provenance=st.text_input('Data source / product identifier (recommended)', placeholder='e.g., NISAR product granule ID and acquisition dates')
        if csv_upload is not None:
            try:
                grid=analyze_aligned_csv(csv_upload.getvalue(),threshold)
                b,a=matrix_from_csv(grid)
                x,y,z=st.columns(3)
                with x:st.metric('Valid paired cells',f'{len(grid):,}')
                with y:st.metric('Mean backscatter Δ',f'{grid.delta_db.mean():+.2f} dB')
                with z:st.metric('Cells above threshold',f'{grid.abs_change_ge_threshold.mean()*100:.1f}%')
                z1,z2=st.columns(2)
                with z1:st.image(sar_gray(b),caption='Before values (user-supplied CSV)',use_container_width=True)
                with z2:st.image(sar_gray(a),caption='After values (user-supplied CSV)',use_container_width=True)
                st.image(change_heatmap(b,a,threshold),caption='Difference: teal indicates positive dB change, orange negative',use_container_width=True)
                st.line_chart(grid[['before_db','after_db']].head(300).reset_index(drop=True))
                st.download_button('⬇️ Download processed grid CSV',grid.to_csv(index=False).encode(),'backscatter_difference.csv','text/csv')
                st.success('Numeric comparison completed. Interpret this as radar backscatter change, not automatically as physical land change.')
                st.session_state['last_uploaded_analysis']={'method':'USER-PROVIDED ALIGNED CSV','rows':len(grid),'mean_delta_db':round(float(grid.delta_db.mean()),3),'source':provenance or '(source not supplied)'}
            except Exception as exc:st.error(f'Cannot analyze the CSV: {exc}')
        st.warning('Required: same area, projection, pixel grid, compatible radar calibration, polarization and viewing geometry. The app does not process raw NISAR HDF5 products or calculate InSAR displacement.')
    else:
        st.markdown('**Compare two exported radar images visually (non-quantitative).**')
        st.caption('Use aligned views of the same area. The app resizes both pictures, which can distort alignment. The difference only reflects changes in image pixel intensity, not calibrated radar backscatter.')
        v1,v2=st.columns(2)
        with v1:before_img=st.file_uploader('Before PNG or JPG',type=['png','jpg','jpeg'],key='photo1')
        with v2:after_img=st.file_uploader('After PNG or JPG',type=['png','jpg','jpeg'],key='photo2')
        if before_img and after_img:
            try:
                b,a,d,mae=align_visual_pair(before_img.getvalue(),after_img.getvalue())
                p1,p2=st.columns(2)
                with p1:st.image(b,caption='Before',use_container_width=True)
                with p2:st.image(a,caption='After',use_container_width=True)
                st.image(d,caption='Visual pixel-difference intensity (orange = greater difference)',use_container_width=True)
                st.metric('Average image-pixel difference',f'{mae:.1f} / 255')
                st.download_button('⬇️ Download visual difference', img_bytes(d), file_name='visual_difference.png', mime='image/png')
                st.session_state['last_uploaded_analysis']={'method':'USER-SUPPLIED IMAGES – VISUAL ONLY','mean_pixel_difference':round(mae,2),'source':'uploaded images'}
            except Exception as exc:st.error(f'Cannot open one of the images: {exc}')
        st.warning('A pixel difference is not a measured flood area, deforestation amount, glacier speed, or surface displacement. Use scientific SAR processing to establish those findings.')

with learn:
    st.subheader('Radar science in simple language')
    cols=st.columns(2)
    cards=[
        ('📡','What is SAR?','Synthetic Aperture Radar sends microwave pulses and measures returning echoes. It can work day or night and through many cloud conditions.'),
        ('🛰️','What is NISAR?','A NASA–ISRO Earth-observing satellite carrying L-band and S-band radar to study land, ice, water and vegetation.'),
        ('📊','Backscatter (dB)','Radar backscatter records how strongly a surface returns the radar signal. Roughness, water, plants, geometry and polarization all matter.'),
        ('🌈','InSAR & phase','Repeat-pass interferometry can reveal subtle line-of-sight surface displacement after careful co-registration and phase processing.'),
        ('🌱','Coherence','Coherence measures similarity between complex radar observations. Low coherence may arise from vegetation changes, water, noise or geometry.'),
        ('🔍','Good comparisons','Match location, acquisition geometry, polarization, calibration and season where possible; verify changes against independent evidence.'),
    ]
    for i,(emoji,title,body) in enumerate(cards):
        with cols[i%2]:
            st.markdown(f'<div class="info-card"><div class="small-label">{emoji} {title}</div><p>{body}</p></div>',unsafe_allow_html=True)
            st.write('')
    st.markdown('### Check your understanding')
    questions=[
        ('What does SAR primarily measure?', ['The sound of Earth','Returned microwave radar signals','Human body temperature'],'Returned microwave radar signals'),
        ('Can SAR often observe land through clouds?', ['Yes','No','Only in daylight'],'Yes'),
        ('What is essential for comparing two raster grids numerically?', ['Same grid and compatible calibration','Different locations','Different projections'],'Same grid and compatible calibration'),
        ('Does a brightness change alone prove ground displacement?', ['Yes','No','Only if it is red'],'No'),
    ]
    with st.form('quiz_form'):
        answers=[]
        for i,(q,options,correct) in enumerate(questions):
            answers.append(st.radio(f'{i+1}. {q}',options,index=None,key=f'quiz_{i}'))
        submitted=st.form_submit_button('Check answers',type='primary')
    if submitted:
        if any(x is None for x in answers):st.warning('Answer all four questions first.')
        else:
            n=sum(ans==q[2] for ans,q in zip(answers,questions))
            st.session_state.quiz_score=n
            st.success(f'You scored {n} / 4.') if n==4 else st.info(f'You scored {n} / 4. Review the cards and try again.')
            for i,((q,options,correct),ans) in enumerate(zip(questions,answers)):
                if ans!=correct: st.caption(f'Question {i+1}: Correct answer — {correct}')
    if st.session_state.quiz_score is not None:
        st.metric('Latest learning score',f'{st.session_state.quiz_score}/4')

with notebook:
    st.subheader('Research notebook')
    st.write('Document what you investigated, the data sources, your interpretation, and the limitations of your conclusions.')
    with st.form('observation_form',clear_on_submit=True):
        scen=st.session_state.get('active_scenario',{})
        title=st.text_input('Investigation title',value=f"{scen.get('kind','Surface change')} — {scen.get('place','selected area')}")
        source_mode=st.selectbox('Evidence type',['Guided simulated example','User-supplied aligned radar CSV','User-supplied images, visual only','Externally processed NISAR observations'])
        source_note=st.text_input('Data source and product IDs',placeholder='NASA/ASF granule IDs or dataset citation; write SIMULATED if using example')
        observation=st.text_area('What did you observe?',placeholder='Describe the locations of changes and their approximate pattern.')
        interpretation=st.text_area('Possible explanation / hypothesis',placeholder='What might produce this radar change? What other evidence do you need?')
        caveat=st.text_area('Uncertainty and limitations',value='A radar change alone does not prove a particular surface process.')
        save=st.form_submit_button('💾 Save observation in this session',type='primary')
    if save:
        if not observation.strip():st.warning('Please write at least one observation before saving.')
        else:
            st.session_state.reports.append({'title':title.strip() or 'Untitled investigation','saved_on':date.today().isoformat(),'area':scen.get('place','Not selected'), 'change_type':scen.get('kind','Not selected'),'before':scen.get('earlier',''), 'after':scen.get('later',''), 'evidence_type':source_mode,'data_citation':source_note.strip() or 'NOT PROVIDED','observations':observation.strip(),'hypothesis':interpretation.strip(),'limitations':caveat.strip()})
            st.success('Observation saved in this browser session. Download your report before closing the app.')
    if st.session_state.reports:
        for idx,entry in enumerate(st.session_state.reports,1):
            with st.expander(f"{idx}. {entry['title']}"):
                st.write('**Evidence:**',entry['evidence_type'],'—',entry['data_citation'])
                st.write('**Observation:**',entry['observations'])
                st.write('**Interpretation:**',entry['hypothesis'])
                st.write('**Limitations:**',entry['limitations'])
        report=['# Dancing with SARs — Research Notebook','',f'Export date: {date.today()}','', 'Training prototype: no claim of automatic NISAR data retrieval.','']
        for entry in st.session_state.reports:
            report += [f"## {entry['title']}",f"- Recorded: {entry['saved_on']}",f"- Location: {entry['area']}",f"- Topic: {entry['change_type']}",f"- Selected dates: {entry['before']} → {entry['after']}",f"- Evidence type: {entry['evidence_type']}",f"- Source: {entry['data_citation']}",f"- Observation: {entry['observations']}",f"- Hypothesis: {entry['hypothesis']}",f"- Limitations: {entry['limitations']}",'']
        st.download_button('⬇️ Download research report (Markdown)','\n'.join(report).encode('utf-8'),'dancing_with_sars_report.md','text/markdown',type='primary')
        st.download_button('⬇️ Download records (JSON)',json.dumps(st.session_state.reports,indent=2,ensure_ascii=False).encode(),'dancing_with_sars_records.json','application/json')
        if st.button('Clear session notes'):
            st.session_state.reports=[];st.rerun()
    else:
        st.info('No observations saved yet. Complete the form above after exploring or comparing data.')

with resources:
    st.subheader('Find real NISAR observations')
    st.markdown('This app is a **research and educational interface**. For genuine NISAR analysis, use observations from the official archives, process them with scientific SAR tools, and document the acquisition IDs.')
    for title,url in NASA_LINKS.items():
        st.markdown(f'**[{title}]({url})**')
    st.markdown('### Data workflow')
    st.markdown('''
1. Open **ASF Vertex** and search for NISAR acquisitions over your study area and selected dates.
2. Sign in with a **NASA Earthdata Login** when the archive requires it.
3. Select compatible L-band products, dates, orbit direction, polarization and geometry.
4. Preprocess and co-register the data in suitable SAR software (e.g., SNAP/QGIS-compatible workflow). Export calibrated aligned grids for brightness change, or use proper interferometric processing for deformation.
5. Import an aligned `before_db` / `after_db` CSV to this application. Record product IDs and limitations in the notebook.
''')
    st.info('As of 2026, NISAR L-band products have been publicly released through ASF. Not every location or date has a matching observation; the app does not claim real-time coverage.')
    st.markdown('### How to use this as a mobile app')
    st.write('Deploy the GitHub repository to Streamlit Community Cloud, then open the public Streamlit URL in your phone browser and choose **Add to Home screen**. This creates a shortcut to the web app, not a native APK.')
    st.caption('Sources: NASA NISAR mission and data pages; Alaska Satellite Facility NISAR Data User Guide and Vertex search. Official images and names belong to their respective owners; this independent prototype is not endorsed by NASA or ISRO.')

st.divider()
st.caption('Dancing with SARs • Grade 11 ICT / NASA Space Apps 2026 • Real-data analysis requires calibrated, co-registered NISAR measurements. Synthetic demos are clearly labeled. Open educational prototype.')

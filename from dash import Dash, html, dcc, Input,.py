from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px



# AREA FUNZIONI

def crea_baseline_grafico(df, tabella=None):

    sistemi = df['Sistema'].unique()
    types = df['Type'].unique()
    sistemi = sorted(sistemi.tolist()*5)
    types = types.tolist()*len(df['Sistema'].unique())



    df_baseline = pd.DataFrame(columns=df.columns)


    if tabella and tabella!='Tabella':
        df_baseline['Sistema'] = sistemi
        df_baseline['Type'] = types
        df_baseline['Tabella'] = tabella
        df_baseline['Severity'] = 'ERROR'
        df_baseline['Esito_Regola'] = 'OK'
        df_grafico = pd.concat([df, df_baseline], axis=0, ignore_index=True)
        return df_grafico
    else:
        df_baseline['Sistema'] = sistemi
        df_baseline['Type'] = types
        df_baseline['Esito_Regola'] = 'OK' #inizializzo ad okay per far si che non venga visualizzato nel conteggio grafico
        df_baseline['Severity'] = 'ERROR' #inizializzo ad error per far si che venga incluso nella groupby
        df_grafico = pd.concat([df, df_baseline], axis=0, ignore_index=True)
        return df_grafico





def crea_dataset(df, sistema, tabella=None):

    df = crea_baseline_grafico(df, tabella)
    tipi_regola = df['Type'].unique()
    df_1 = df[df['Sistema'] == sistema]
    if tabella and tabella!='Tabella':
        df_2 = df_1[df_1['Tabella'] == tabella]
        df_merge = pd.DataFrame(columns=['Tabella', 'Type', 'KO'])
        df_merge['Type'] = tipi_regola
        df_merge['Tabella'] = tabella
        df_3 = pd.merge(df_merge, df_2[df_2['Tabella']==tabella], how = 'left')
        df_3['Esito_Regola'] = df_3['Esito_Regola'].fillna('')
        df_3['KO'] = df_3['Esito_Regola'].apply(lambda x: 0 if x=='' or x=='OK' else 1)   
        return df_3
    else:      
        df_2 = df_1.groupby(['Type', 'Severity'])['Esito_Regola'].apply(lambda x: (x == 'KO').sum()).reset_index(name='KO')
        df_2 = df_2.sort_values(by=['Severity'], ascending=[True])
        return df_2






external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Questo script ha lo scopo di simulare un'applicazione Dash che mostra dei grafici in crossfiltering


# Carico il dataset, ne ho salvato uno di prova sulla mia area di lavoro.

df = pd.read_csv('/Users/federico/Desktop/VSC/set_dati/dati.csv')








# il dataset df è costruito in modo tale da ospitare dati su 5 dimensioni: 'Sistema', 'Tabella', 'Regola', 'Type', 'Esito_Regola'

# devo creare un'applicazione dash che mi permetta di visualizzare i dati in crossfiltering, come primo elemento voglio un menù dropdown che funga da filtro
# per andare a selezionare un determinato sistema. Il menù dropdown deve essere costruito in modo tale da mostrare solo i sistemi presenti nel dataset.

# creo una lista di sistemi presenti nel dataset

lista_sistemi = df['Sistema'].unique()

# creo un'applicazione dash

app = Dash(__name__, external_stylesheets=external_stylesheets)

# creo il layout dell'applicazione

app.layout = html.Div([
                html.H1('Dashboard'),
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='filtro-sistema',
                            options=[{'label': i, 'value': i} for i in lista_sistemi],
                            placeholder='Seleziona un sistema',
                            value='Sistema'
                            )
                        ],
                        style={'width': '48%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(
                            id='filtro-tabella',
                            placeholder='Seleziona una tabella',
                            value='Tabella',
                            )
                        ],
                        style={'width': '48%', 'display': 'inline-block'}),             
                        ]),
                html.Div([
                    dcc.Graph(id='grafico-1')
                    ], style = {'width': '48%', 'display': 'inline-block', 'padding': '0 20'}),
                    ])
                    

# ora voglio creare un secondo filtro che mi permetta di selezionare una determinata tabella, questo filtro deve essere costruito in modo tale da mostrare
# solo le tabelle presenti nel dataset che sono associate al sistema selezionato nel primo filtro. Inoltre non deve essere possibile selezionare una tabella
# se non è stato selezionato un sistema nel primo filtro.

# creo una lista di tabelle associate al sistema selezionato nel primo filtro

@app.callback(
    Output('filtro-tabella', 'options'),
    Input('filtro-sistema', 'value'))
def update_dropdown_tabella(sistema):
    lista_tabelle = df[df['Sistema'] == sistema]['Tabella'].unique()
    return [{'label': i, 'value': i} for i in lista_tabelle]


# Il primo filtro deve aggiornare un grafico a barre che mostra, per Type di regola (errore, warning, info), il numero di regole in stato 'KO' (da esito_regola) associate al sistema.
# Il numero di regole viene visualizzato sulla coordinata y e stratificato per severity

@app.callback(
    Output('grafico-1', 'figure'),
    Input('filtro-sistema', 'value'),
    Input('filtro-tabella', 'value'))
def update_grafico_1(sistema,tabella):

    #ogni volta che cambio l'input, devo creare una funzione che genera un dataset. La funzione che genera il dataset deve avere come input il nome del sistema ed il nome della tabella
    #come parametro opzionale, in modo tale da poterla utilizzare anche se non è stata selezionata una tabella. La funzione deve restituire un dataset che contiene il numero di regole
    #in stato KO per ogni Type di regola e per ogni severity.



    #controllo inoltre che, se rimane in canna un valore di tabella che non corrisponde al sistema selezionato, la tabella viene considerata = 'Tabella', ovvero la defaulto
    #trovo l'indice in cui df['Tabella'] = tabella. Poi ricarico il dataset
    if tabella and tabella!='Tabella':
        index = df[df['Tabella'] == tabella].index
        if sistema!= df['Sistema'][index[0]]:
            tabella = 'Tabella'
    dataset = crea_dataset(df, sistema, tabella)

    #sorta il dataset per severity



    # La mancanza di severity in una tabella potrebbe provocare l'assenza della label in fase di visualizzazione grafica. Per evitare che il problema si verifichi,
    # ho aggiunto manualmente le casistiche di severity mancanti nel dataset. Il dataset di riferimento è stato aumentato con delle righe fake che consentono di andare
    # a creare le casistiche di severity mancanti. Lo stesso ragionamento è stato utilizzato per il Type di regola. Tutti gli elementi fake sono stati classificati come OK
    # in modo tale da non influenzare il conteggio delle regole in stato KO e di conseguenza la visualizzaione grafica.

    dataset = dataset.sort_values(by=['Severity'], ascending=[True])
    
    dataset.loc[-1,'Severity'] = 'WARNING'
    dataset.loc[-2,'Severity'] = 'INFO'

    dataset = dataset.sort_values(by=['Severity'], ascending=[True])

    color_dict = {
        'WARNING': '#E0B0FF',
        'ERROR': '#DA70D6',
        'INFO': '#CCCCFF'
}






    # df_2 contiene il numero di regole in stato KO per ogni Type di regola e per ogni severity, ora devo creare un grafico a barre che mostri questi dati
    # il grafico a barre deve avere sull'asse x il Type di regola, sull'asse y il numero di regole in stato KO e deve essere stratificato per severity, quindi
    # ogni barra deve essere divisa in 3 parti impilate una sopra l'altra, una per ogni severity. 
    # alla base devono sempre esserci gli errori, poi i warning e infine le info.

    fig = px.bar(dataset, x='Type', y='KO', color='Severity', barmode='stack', color_discrete_map=color_dict)
    fig.update_xaxes(title_text='Control Type')
    fig.update_yaxes(title_text='Number of KO rules')
    # aggiungo il titolo al grafico, il titolo deve essere costruito in modo tale da mostrare il sistema e la tabella selezionati nei filtri, se non è stata selezionata

    if tabella and tabella!='Tabella' and sistema and sistema!='Sistema':  
        fig.update_layout(title_text=f'{sistema}.{tabella}', title_x=0.5, title_font_size=20, legend_title_text='Severity')
    elif sistema and sistema!='Sistema':
        fig.update_layout(title_text=f'{sistema}', title_x=0.5, title_font_size=20, legend_title_text='Severity')
    else:
        fig.update_layout(title_text='', title_x=0.5, title_font_size=20, legend_title_text='Severity')


    return fig




if __name__ == '__main__':
    app.run(debug=True)

    
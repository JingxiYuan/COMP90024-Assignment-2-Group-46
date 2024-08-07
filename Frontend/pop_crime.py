import pandas as pd
from shapely.geometry import Point,MultiPolygon
from shapely.ops import nearest_points
import folium
from ipywidgets import Dropdown, Output, HBox
from IPython.display import display
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

class Pop_crime:
    def __init__(self):
        pass


    def pop_df(self, pop_source):
        pop_df1 = pd.DataFrame(pop_source[0])
        pop_df1 = pop_df1.loc[['coordinates']]
        for i in pop_source[1:]:
            pop_df2 = pd.DataFrame(i)
            pop_df2 = pop_df2.loc[['coordinates']]
            pop_df1 = pd.concat([pop_df1, pop_df2])
        pop_df1['LGA_name'] = pop_df1['LGA_name'].str[:-4]
        pop_df1.reset_index(drop=True, inplace=True)
        return pop_df1

    def crime_df(self, crime_source):
        crime_df1 = pd.DataFrame([crime_source[0]])
        crime_df1.reset_index(drop=True, inplace=True)
        for i in crime_source[1:]:
            crime_df2 = pd.DataFrame([i])
            crime_df2.reset_index(drop=True, inplace=True)
            crime_df1 = pd.concat([crime_df1, crime_df2])
        crime_df1 = crime_df1.reset_index(drop=True)
        crime_df1 = crime_df1.drop(crime_df1[crime_df1['LGA_name'] == 'Melbourne'].index)
        return crime_df1

    def merge_df(self, pop_df1, crime_df1):
        selected_rows = pop_df1[['LGA_name', 'population', 'age_group']].groupby("LGA_name").agg({'population': 'sum'})
        selected_rows = selected_rows.reset_index(drop=False)
        type_crime = pd.merge(selected_rows[['LGA_name', 'population']],
                              crime_df1[['LGA_name', 'offence_count', 'offence_subdiv']], on=['LGA_name'], how='inner')
        type_crime = type_crime.drop_duplicates()
        type_crime = type_crime.groupby(['LGA_name', 'offence_subdiv']).agg(
            {'population': 'first', 'offence_count': 'sum'}).reset_index()
        return type_crime

    def object_to_geojson(self, data, geo, pro):
        feature_collection = {"type": "FeatureCollection", "features": []}
        data_list = data.index.tolist()
        for item in data_list:
            feature = {"type": "Feature", "geometry": [], "properties": []}
            geometry = {"type": "MultiPolygon", "coordinates": data.loc[item][geo]}
            properties = {pro: data.loc[item][pro]}
            feature["properties"] = properties
            feature["geometry"] = geometry
            feature_collection["features"].append(feature)

        return feature_collection

    def calculate_centroid(self, coordinates):
        """Calculate the centroid of a polygon given its coordinates."""
        x_sum = 0
        y_sum = 0
        n = len(coordinates)
        for x, y in coordinates:
            x_sum += x
            y_sum += y
        centroid_x = x_sum / n
        centroid_y = y_sum / n
        return (centroid_x, centroid_y)

    def calculate_multipolygon_midpoint(self, multipolygon_coords):
        """Calculate a midpoint for a multipolygon based on the average of polygon centroids."""
        total_x = 0
        total_y = 0
        count = 0
        for polygon_coords in multipolygon_coords:
            for polygon_coord in polygon_coords:
                centroid_x, centroid_y = self.calculate_centroid(polygon_coord)
                total_x += centroid_x
                total_y += centroid_y
                count += 1
            if count == 0:
                return None
        return (total_y / count, total_x / count)

    def preprocessing_bom(self, bom_df, selected_rows):
        bom_list = bom_df.index.tolist()
        select_list = selected_rows.index.tolist()
        bom_df = bom_df[['STATION', 'wind_spd_kmh', 'Location']]
        bom_df['coordinates'] = None
        for i in bom_list:
            bom_df.at[i, 'coordinates'] = [bom_df.loc[i]['Location']['lon'], bom_df.loc[i]['Location']['lat']]
        bom_df = bom_df.groupby('STATION').agg({'wind_spd_kmh': 'mean', 'coordinates': 'first'}).reset_index()
        bom_df['geometry'] = None
        bom_list = bom_df.index.tolist()
        for pop_geo in select_list:
            for bom_geo in bom_list:
                if Point(bom_df.loc[bom_geo]['coordinates']).within(
                        MultiPolygon(selected_rows.loc[pop_geo]['geometry'])):
                    bom_df.at[bom_geo, 'geometry'] = selected_rows.loc[pop_geo]['geometry']
        bom_df = bom_df.dropna().reset_index(drop=True)
        bom_df['PM2.5'] = 0
        bom_df['Particles'] = 0
        return bom_df

    def preprocessing_epa(self, epa_df):
        epa_df = epa_df[(epa_df['healthParameter'] == 'PM2.5') | (epa_df['healthParameter'] == 'Particles')].reset_index(drop=True)
        epa_list = epa_df.index.tolist()
        for epa in epa_list:
            epa_df.at[epa, 'location'] = [epa_df.loc[epa]['location']['lon'], epa_df.loc[epa]['location']['lat']]
        return epa_df

    def find_nearest_station(self, epa_df, bom_df):
        distance_threshold = 1
        epa_list = epa_df.index.tolist()
        for index in epa_list:
            min_distance = float('inf')
            assigned_station = None
            pm_type = epa_df.loc[index]['healthParameter']
            for indexb in range(0, len(bom_df)):
                nearest_pt = \
                nearest_points(Point(epa_df.loc[index]['location']), MultiPolygon(bom_df.loc[indexb]['geometry']))[1]
                distance = Point(epa_df.loc[index]['location']).distance(nearest_pt)

                if distance < min_distance:
                    min_distance = distance
                    assigned_station = bom_df.loc[indexb]['STATION']

            if min_distance <= distance_threshold:
                if pm_type == 'PM2.5':
                    index_change = bom_df[bom_df['STATION'] == assigned_station]['PM2.5'].index[0]
                    bom_df.at[index_change, 'PM2.5'] = bom_df.at[index_change, 'PM2.5'] + 1
                else:
                    index_change = bom_df[bom_df['STATION'] == assigned_station]['Particles'].index[0]
                    bom_df.at[index_change, 'Particles'] = bom_df.at[index_change, 'Particles'] + 1
        return bom_df

    def draw_mpowind(self, location, feature_collection, bom_df):
        m_po_wind = folium.Map(location=location, titles="pollution and windspeed", zoom_start=11)
        folium.Choropleth(
            geo_data=feature_collection,
            name='choropleth',
            data=bom_df,
            columns=['STATION', 'wind_spd_kmh'],
            key_on='feature.properties.STATION',
            fill_color='YlGnBu',
            fill_opacity=1,
            line_opacity=1,
            legend_name='Population by Country'
        ).add_to(m_po_wind)
        return m_po_wind
    def add_layer(self, bom_df, type, color, map, show):
        layer1 = folium.FeatureGroup(name= type +' Layer', show= show)
        for item in range(0, len(bom_df)):
            folium.CircleMarker(
                location=[bom_df.at[item, 'coordinates'][1], bom_df.at[item, 'coordinates'][0]],
                radius=bom_df.at[item, type] / 5,
                popup=type+' Count: {}'.format(bom_df.at[item, type]),
                color= color,
                fill=True,
                fill_color=color
            ).add_to(layer1)
        layer1.add_to(map)

    def draw_pmap(self, location, fea, selected_rows, crime_geo):
        m_pop = folium.Map(location=location, titles="Stamen Terrain", zoom_start=11)
        folium.Choropleth(
            geo_data=fea,
            name='choropleth',
            data=selected_rows,
            columns=['LGA_name', 'population'],
            key_on='feature.properties.LGA_name',
            fill_color='YlGnBu',
            fill_opacity=1,
            line_opacity=1,
            legend_name='Population by Country'
        ).add_to(m_pop)
        crime_geo['centoroid'] = None
        geo_list = crime_geo.index.tolist()
        for item in geo_list:
            crime_geo.at[item, 'centoroid'] = self.calculate_multipolygon_midpoint(crime_geo.loc[item]['geometry'])
            folium.CircleMarker(
                location=crime_geo.at[item, 'centoroid'],
                radius=crime_geo.at[item, 'offence_count'] / 1000,
                popup='Crime Count: {}'.format(crime_geo.at[item, 'offence_count']),
                color='red',
                fill=True,
                fill_color='red'
            ).add_to(m_pop)
        return m_pop
    def crime_pears(self,crime_list, type_crime, crime_pear):
        for crime in crime_list[1:]:
            pear = type_crime.loc[type_crime['offence_subdiv'] == crime][['population', 'offence_count']].corr().loc[
                'population', 'offence_count']
            if np.isfinite(pear):
                crime_pear['pearson'].append(pear)
            else:
                crime_pear['pearson'].append(0)
        return crime_pear
    def show_offence(self, crime_list, type_crime):
        choose_crime = Dropdown(
            options=crime_list,
            description='Offence types:',
        )
        output_crime = Output()

        def choiceY(change):
            with output_crime:
                output_crime.clear_output()
                crime_type = type_crime.loc[type_crime['offence_subdiv'] == change.new][['population', 'offence_count']]
                print(change.new, ": pearson is", crime_type.corr().loc['population', 'offence_count'])

                # scatter plot
                res = sns.regplot(x=type_crime.loc[type_crime['offence_subdiv'] == change.new]['population'],
                            y=type_crime.loc[type_crime['offence_subdiv'] == change.new]
                            ['offence_count'], scatter=True, ci=None, line_kws={"color": "red"})
                plt.title(f"{change.new} VS. Population", fontdict={"fontsize":16,"fontweight":"bold"})
                plt.show()

        choose_crime.observe(choiceY, names='value')

        ui = HBox([choose_crime])

        display(ui)
        display(output_crime)
    def draw_radar(self, crime_pear):
        crime_pear = pd.DataFrame(crime_pear)
        crime_pear['types'] = crime_pear['types'].apply(lambda x: x[:3])
        labels = np.array(crime_pear['types'])
        stats = crime_pear['pearson'].values

        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()

        stats = np.concatenate((stats, [stats[0]]))
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.fill(angles, stats, color='red', alpha=0.25)
        ax.plot(angles, stats, color='red', linewidth=2)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_yticklabels([])

        for label, angle, stat in zip(labels, angles, stats):
            ax.text(angle, stat, f'{stat:.2f}', ha='center', va='center', color='black', fontsize=10)

        ax.set_title('Pearson Correlation Between Crime Types and Population', size=15, color='red', y=1.1)

        plt.show()

    def get_masto(self, ma_inbom_source, ma_bom_source):
        df_bom = pd.DataFrame(ma_inbom_source)
        df_mastodon = pd.DataFrame(ma_bom_source)

        df_bom.rename(columns={'DATE': 'created_at'}, inplace=True)

        df_bom['created_at'] = pd.to_datetime(df_bom['created_at'])
        df_mastodon['created_at'] = pd.to_datetime(df_mastodon['created_at'])

        merged_df = pd.merge(df_bom, df_mastodon, on='created_at', how='inner')
        merged_df['rain_trace'] = pd.to_numeric(merged_df['rain_trace'], errors='coerce')
        merged_df = merged_df.dropna(subset=['rain_trace'])
        return merged_df

    def draw_mastpie(self, dataframe):
        greater_than_5 = dataframe[dataframe['sentiment'] >= 5]
        less_than_5 = dataframe[dataframe['sentiment'] < 5]

        counts = [len(greater_than_5), len(less_than_5)]
        labels = ['Sentiment > 5', 'Sentiment < 5', ]

        plt.figure(figsize=(8, 8))
        plt.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#ff9999', '#66b3ff'])
        plt.title('Distribution of Contents by Sentiment', pad=20)
        plt.axis('equal')
        plt.show()

    def draw_mastbom(self, merged_df):
        filtered_df = merged_df[merged_df['sentiment'] != 5]

        variables = ['filter', 'rain_trace', 'air_temp', 'rel_hum', 'wind_spd_kmh', 'press']
        sentiments = filtered_df['sentiment'].unique()

        bins_dict = {
            'rain_trace': np.arange(0, 10, 1),
            'air_temp': np.arange(0, 40, 2),
            'rel_hum': np.arange(0, 100, 10),
            'wind_spd_kmh': np.arange(0, 50, 5),
            'press': np.arange(1000, 1050, 5)
        }
        choose_filter = Dropdown(
            options=variables,
            description='filter types:',
        )
        output_filter = Output()

        def choiceF(change):
            with output_filter:
                output_filter.clear_output(wait=True)
                variable = change.new
                fig, ax = plt.subplots(figsize=(14, 8))
                width = 0.2

                colors = plt.cm.viridis(np.linspace(0, 1, len(sentiments)))

                for i, sentiment in enumerate(sentiments):
                    data = filtered_df[filtered_df['sentiment'] == sentiment][variable].dropna()
                    if not data.empty:
                        counts, bins = np.histogram(data, bins=bins_dict[variable])
                        idxs = list(range((len(counts)-1),-1,-1))
                        for j in idxs:
                        #print(len(counts))
                        #print(counts.shape)
                            if counts[j]==0:
                                counts = np.delete(counts,j)
                                bins = np.delete(bins,j)
                        
                            elif counts[j]!=0:
                                break
                        ax.bar(bins[:-1] + i * width, counts, width=width, alpha=0.7, label=f'Sentiment {sentiment}',
                               color=colors[i])

                ax.set_title(f'Distribution of {variable} by Sentiment (excluding sentiment 5)', fontsize=16,fontweight='bold')
                ax.set_xlabel(variable,fontsize=14)
                ax.set_ylabel('Count',fontsize=14)
                ax.legend(title='Sentiment')
                plt.xticks(bins[:-1] + width * len(sentiments) / 2, [f'{b:.1f}' for b in bins[:-1]], rotation=0)
                plt.tight_layout()

                plt.show()

        choose_filter.observe(choiceF, names='value')

        ui = HBox([choose_filter])

        display(ui)
        display(output_filter)
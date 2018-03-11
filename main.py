import pandas as pd
import sqlalchemy
import numpy as np

from bokeh.io import curdoc
from bokeh.palettes import Category20
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, CategoricalColorMapper
from bokeh.models.widgets import TextInput, Select, RangeSlider, Slider, CheckboxGroup, Panel, Tabs #, DataTable, TableColumn
from bokeh.plotting import figure

## Setup data and SQL

engine = sqlalchemy.create_engine('sqlite:///../test.db')
metadata = sqlalchemy.MetaData()
metadata.reflect(bind=engine)
dmo = metadata.tables['dmo']
disk = metadata.tables['disk']
conn = engine.connect()

df = pd.read_sql(sqlalchemy.select([dmo]).where(dmo.c.vmax > 100),conn)
df2 = pd.read_sql(sqlalchemy.select([disk]).where(disk.c.vmax > 100),conn)
source = ColumnDataSource(data={'x' : df['vmax'], 'y' : df['mvir'], 'host_id' : df['host_id'].astype(str)})
source2 = ColumnDataSource(data={'x' : df2['vmax'], 'y' : df2['mvir'], 'host_id' : df2['host_id'].astype(str)})
plot_data = ColumnDataSource(data={'x' : [], 'y' : []})
plot_data2 = ColumnDataSource(data={'x' : [], 'y' : []})

## Build Bokeh inputs and callbacks

col_exclude = ['x', 'y', 'z', 'index', 'host_id']
col_allow = [i for i in df.columns if i not in col_exclude]

sql_query = TextInput(value="where vmax > 100", title='SQL filter:')
log_axes = CheckboxGroup(labels=["Log(x)", "Log(y)"], active=[])
column1 = Select(title="X-axis Data:", value="vmax", options=col_allow)
column2 = Select(title="Y-axis Data:", value="mvir", options=col_allow)
plot_type = Select(title="Standard plots:", value="Infall", options=["Infall", "Mvir","Vmax", "Vpeak"]) # Add AM maybe?

labels_dict = dict(vmax='Vmax (km/s)', mvir='Mvir (M_sun)', rvir='Rvir (kpc)', 
				   dist='Dist from MW (kpc)', peri='Pericenter (kpc)', vpeak='Vpeak (km/s)',
				   vr='Radial Velocity (km/s)', vtan='Tangential Velocity (km/s)', infall='Infall Time (Gyrs)')

hover = HoverTool(tooltips=[('Host', '@host_id'),
							('{}'.format(column1.value), '@x'),
							('{}'.format(column2.value), '@y')])

id_list = df['host_id'].unique().astype(str).tolist()

color_mapper = CategoricalColorMapper(factors=id_list, palette=Category20[12])

p = figure(x_axis_label="Vmax (km/s)", y_axis_label="Mvir (M_sun)")
p.circle('x','y', source=source, 
		 color='black',#dict(field='host_id', transform=color_mapper), 
		 legend='DMO',#'host_id',
		 size=7)
p.circle('x', 'y', source=source2,
		 color='magenta',
		 legend='Disk',
		 size=7,
		 fill_alpha=0.5)
p.add_tools(hover)
p.legend.location = 'top_left'
p.legend.click_policy = 'hide'
p.legend.background_fill_alpha = 0.5

def query_change(attr, old, new):
	'''
		This function takes the SQL query and alters it slightly to make
		the query apply to both the DMO and Disk tables
	'''
	s = 'select * from dmo ' + sql_query.value
	s2 = 'select * from disk ' + sql_query.value

	global df, df2
	df = pd.read_sql(s,conn)
	df2 = pd.read_sql(s2,conn)
	column1.options = [i for i in df.columns if i not in col_exclude]
	column2.options = [i for i in df.columns if i not in col_exclude]
	column_change([], [], [])
	create_line_plot([],[],plot_type.value) 

def scale_axes(attr, old, new):
	new_x = source.data['x']
	new_y = source.data['y']
	new_x2 = source2.data['x']
	new_y2 = source2.data['y']

	if (0 in new) and (0 not in old):
		new_x = np.log10(new_x)
		new_x2 = np.log10(new_x2)
		p.xaxis.axis_label = "Log10  " + labels_dict[column1.value]
	if (0 not in new) and (0 in old):
		new_x = df[column1.value]
		new_x2 = df2[column1.value]
		p.xaxis.axis_label = labels_dict[column1.value]
		
	if (1 in new) and (1 not in old):
		new_y = np.log10(new_y)
		new_y2 = np.log10(new_y2)
		p.yaxis.axis_label = "Log10  " + labels_dict[column2.value]
	if (1 not in new) and (1 in old):
		new_y = df[column2.value]
		new_y2 = df2[column2.value]
		p.yaxis.axis_label = labels_dict[column2.value]

	source.data = {'x' : new_x,
				   'y' : new_y, 
				   'host_id' : df['host_id'].astype(str)}

	source2.data = {'x' : new_x2,
				   	'y' : new_y2, 
				   	'host_id' : df2['host_id'].astype(str)}

def column_change(attr, old, new):
	new_x = df[column1.value]
	new_y = df[column2.value]
	new_x2 = df2[column1.value]
	new_y2 = df2[column2.value]

	if (0 in log_axes.active):
		p.xaxis.axis_label = "Log10  " + labels_dict[column1.value]
		new_x = np.log10(df[column1.value])
		new_x2 = np.log10(df2[column1.value])
	else:
		p.xaxis.axis_label = labels_dict[column1.value]

	if (1 in log_axes.active):
		p.yaxis.axis_label = "Log10  " + labels_dict[column2.value]
		new_y = np.log10(df[column2.value])
		new_y2 = np.log10(df2[column2.value])
	else:
		p.yaxis.axis_label = labels_dict[column2.value]

	hover.tooltips = [('Host', '@host_id'),
					  ('{}'.format(column1.value), '@x'),
					  ('{}'.format(column2.value), '@y')]

	source.data = {'x' : new_x, 
				   'y' : new_y, 
				   'host_id' : df['host_id'].astype(str)}

	source2.data = {'x' : new_x2,
				   	'y' : new_y2, 
				   	'host_id' : df2['host_id'].astype(str)}


def create_line_plot(attr, old, new):
	if new == "Infall":
		t = df['infall'].loc[df.infall < 13.8]
		hist, edges = np.histogram(t, bins=100, range=(0,13))
		hist = (np.sum(hist) - np.cumsum(hist))/np.sum(hist)
		plot_data.data = {'x' : edges[:-1],
						  'y' : hist}
		t = df2['infall'].loc[df2.infall < 13.8]
		hist, edges = np.histogram(t, bins=100, range=(0,13))
		hist = (np.sum(hist) - np.cumsum(hist))/np.sum(hist)
		plot_data2.data = {'x' : edges[:-1],
						  'y' : hist}
		p2.xaxis.axis_label = labels_dict['infall']
		p2.yaxis.axis_label = ""
	elif new == "Mvir":
		t = np.log10(df['mvir'])
		hist, edges = np.histogram(t, bins=100)
		hist = np.log10(np.sum(hist) - np.cumsum(hist))
		plot_data.data = {'x' : edges[:-1],
						  'y' : hist}
		t = np.log10(df2['mvir'])
		hist, edges = np.histogram(t, bins=100)
		hist = np.log10(np.sum(hist) - np.cumsum(hist))
		plot_data2.data = {'x' : edges[:-1],
						  'y' : hist}
		p2.xaxis.axis_label = "Log10  " + labels_dict['mvir']
		p2.yaxis.axis_label = ""
	elif new == "Vmax":
		t = np.log10(df['vmax'])
		hist, edges = np.histogram(t, bins=100)
		hist = np.log10(np.sum(hist) - np.cumsum(hist))
		plot_data.data = {'x' : edges[:-1],
						  'y' : hist}
		t = np.log10(df2['vmax'])
		hist, edges = np.histogram(t, bins=100)
		hist = np.log10(np.sum(hist) - np.cumsum(hist))
		plot_data2.data = {'x' : edges[:-1],
						  'y' : hist}
		p2.xaxis.axis_label = "Log10  " + labels_dict['vmax']
		p2.yaxis.axis_label = ""
	else:
		t = np.log10(df['vpeak'])
		hist, edges = np.histogram(t, bins=100)
		hist = np.log10(np.sum(hist) - np.cumsum(hist))
		plot_data.data = {'x' : edges[:-1],
						  'y' : hist}
		t = np.log10(df2['vpeak'])
		hist, edges = np.histogram(t, bins=100)
		hist = np.log10(np.sum(hist) - np.cumsum(hist))
		plot_data2.data = {'x' : edges[:-1],
						  'y' : hist}
		p2.xaxis.axis_label = "Log10  " + labels_dict['vpeak']
		p2.yaxis.axis_label = ""

p2 = figure()
p2.line('x', 'y', source=plot_data, color='black', legend='DMO')
p2.line('x', 'y', source=plot_data2, color='magenta', legend='Disk')
p2.legend.click_policy = 'hide'
    
sql_query.on_change('value', query_change)
log_axes.on_change('active', scale_axes)
column1.on_change('value', column_change)
column2.on_change('value', column_change)
plot_type.on_change('value', create_line_plot)

layout1 = row(column(sql_query, log_axes, column1, column2, plot_type), p, p2)
# layout2 = row(column(sql_query, log_axes, plot_type), p2)

create_line_plot([],[],'Infall')

curdoc().add_root(layout1)

# plots = column()
# data_table = DataTable(source=source,
#                        columns=[Table])
# tab1 = Panel(child=plots, title='Figures')
# tab2 = Panel(child=data_table, title='Table')
# tabs = Tabs(tabs=[tab1,tab2])



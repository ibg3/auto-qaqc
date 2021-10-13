"""
CoRNy Figures
    Functions for Plotting and output
"""
import pandas as pd
import numpy as np
import os
import re
import matplotlib
import matplotlib.pyplot as plt

# Uncomment the following if you need geo features

#import cartopy
#import cartopy.crs as ccrs
#import cartopy.feature as cpf
#import matplotlib as mpl
#from matplotlib.pyplot import figure, show
#import matplotlib.ticker as mticker
#from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
# image spoof
#import cartopy.io.img_tiles as cimgt
#from urllib.request import urlopen, Request
#from PIL import Image


def plot_diurnal(data, var='moisture', var_title='Volumetric water content', var_units='(in cm$^3$/cm$^3$)', y_range=(0,0.5)):
    D = data.copy()
    D['Time'] = D.index.map(lambda x: x.strftime("%H:%M"))
    D = D.groupby('Time').describe().unstack()
    with Fig(fig, title='Diurnal cycle of %s' % var_title, ylabel='%s %s' % (var_title, var_units), ylim=y_range) as ax:
        ax.fill_between(D[var]['mean'].index, D[var]['25%'], D[var]['75%'], color='C0', alpha=0.2, lw=0, step='post', label='Quantiles 25%--75%')
        ax.plot(D[var]['mean'].index, D[var]['mean'], color='C0', drawstyle='steps-post', label='Average %s' % var_title)
        ax.legend()
        ax.set_xticks(range(0,24))
        ax.set_xticklabels(range(0,24))
        ax.set_xlim(0,23)


"""
    plot_all(df, rows, cols)
    = fig
    Takes a data frame and plots all columns in r x c subplots.
    Can skip certain columns.
"""
def plot_all(D, nrow=1, ncol=4, skip=[]):
    fig = plt.figure(figsize=(ncol*4, nrow*3))
    fig.subplots_adjust(hspace=0.4, wspace=0.3)
    i = 0
    k = 0
    for i in D.columns:
        if not i in skip:
            k += 1
            plt.subplot(nrow, ncol, k)
            ax = D[i].plot(title=i)
            ax.set_xlabel("")
    return(fig)

def plot_errorbar(x, y, xerr=None, yerr=None, fmt='s', ecolor='black', elinewidth=1, capsize=3, mfc='white', mec='black', ms=7, mew=1, alpha=1):
    return(plt.errorbar(x, y, xerr=xerr, yerr=yerr,
                        fmt=fmt, ecolor=ecolor, elinewidth=elinewidth, capsize=capsize,
                        mfc=mfc, mec=mec, ms=ms, mew=mew, alpha=alpha))


# Maps

def Shapemap(lons=None, lats=None, var=None, extent=[5.5,15.5,47.2,55.2], size=(6,4), method=None,
             contour_levels=None, title='', points=None, grid=False, cmap_name='Spectral', colorbar=True,
             save=None, save_dpi=300, point_size=1, point_color='black', point_marker='o',  ticks_sep=0.05, clim=None,
             resolution='50m', resolution_fine='10m', counties=True,
             ocean=True, land=False, lakes=True, rivers=True, borders=True, coast=True):

    fig, ax = plt.subplots(figsize = size)
    ax = plt.axes(projection=cartopy.crs.PlateCarree())
    if title: ax.set_title(title)

    if clim is None: clim = (None, None)
    colormap = mpl.cm.get_cmap(cmap_name)
    #colormap.set_over("red")
    #colormap.set_under("blue")
    if method=='contour':
        im = ax.contourf(lons, lats, var, levels=contour_levels,
                          transform=ccrs.PlateCarree(), cmap=colormap,
                          extend="both",    # do not go beyond zmin/zmax
                          antialiased=False)
        im.cmap.set_under('white')
    elif method=='raster':
        im = ax.pcolormesh(lons, lats, var, transform=ccrs.PlateCarree(), cmap=colormap, rasterized=True)
        im.cmap.set_under('white')
    elif method=='points':
        if var is None:
            im = ax.scatter(lons, lats, c=point_color, s=point_size, marker=point_marker, zorder=2, edgecolors='red', linewidths =2)
            im = ax.scatter(lons, lats, c='red', s=point_size/10, marker=point_marker, zorder=2, edgecolors='none')
        else:
            im = ax.scatter(lons, lats, c=var, cmap=colormap, vmin=clim[0], vmax=clim[1], s=point_size, zorder=2)
            im.cmap.set_under('white')
        #ax.stock_img()
    elif method=='lines':
        im = ax.plot(lons, lats, color='red')
        #ax.stock_img()


    # Features
    if ocean:   ax.add_feature(cpf.OCEAN.with_scale(resolution)) # ocean background and coast shape
    if land:    ax.add_feature(cpf.LAND.with_scale(resolution))  # land background and shape
    if lakes:   ax.add_feature(cpf.LAKES.with_scale(resolution_fine))
    if rivers:  ax.add_feature(cpf.RIVERS.with_scale(resolution_fine), lw=0.5)
    if counties:
        counties = cpf.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lines',
            scale=resolution_fine, facecolor='none')
        ax.add_feature(counties, edgecolor='black', lw=0.5, alpha=0.5)
    if borders: ax.add_feature(cpf.BORDERS.with_scale(resolution), lw=0.5)
    if coast:   ax.add_feature(cpf.COASTLINE.with_scale(resolution), lw=0.5)


    # Points
    if not points is None:
        for i, p in points.iterrows():
            ax.scatter(p['lon'], p['lat'], lw=1, s=10, color=p['color'])
            ax.text(p['lon']+0.01*(extent[1]-extent[0]), p['lat'], str(p['label']), color=p['color'], verticalalignment='center')

    # Grid
    gl = ax.gridlines(draw_labels=True, color="black", alpha=0.3, lw=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xlines = grid
    gl.ylines = grid
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    #gl.xlocator = mticker.FixedLocator(np.arange(int(extent[0]),int(extent[1])+1))
    #gl.ylocator = mticker.FixedLocator(np.arange(int(extent[2]),int(extent[3])+1))
    gl.xlocator = mticker.FixedLocator(np.arange(np.round(extent[0],2),np.round(extent[1],2)+1, ticks_sep))
    gl.ylocator = mticker.FixedLocator(np.arange(np.round(extent[2],2),np.round(extent[3],2)+1, ticks_sep))
    gl.xlabel_style = {'size': '7'}
    gl.ylabel_style = {'size': '7'}

    if colorbar and not method is None:
        cb = plt.colorbar(im, extend="both")
        cb.set_label(title, rotation=270, labelpad=20)

    ax.set_extent(extent)

    if not save is None:
        plt.savefig(save, bbox_inches='tight', frameon=False, dpi=save_dpi)
        plt.close(fig)

    return(fig, ax)

# Make boxplots of something over luse data
# Requires .get_from_raster('luse', file) to be called beforehand
def luse_plot(data, var, label=None, format_str="%.2f",
              luse_cat=['urban', 'agriculture', 'wetland', 'forest', 'water'],
             luse_col=['red', 'orange', 'lightblue', 'green', 'blue']):
    data = [data.loc[data.luse_str==l, var].dropna() for l in luse_cat]
    with Fig(size=(5,4), grid=False, legend=False):
        B = Fig.ax.boxplot(data, patch_artist=True, medianprops=dict(linestyle='--', color='black', linewidth=1))
        for b, color in zip(B['boxes'], luse_col):
            b.set(color=color, facecolor=color)
        for i, m in enumerate([x.median() for x in data]):
            if np.isfinite(m):
                text = Fig.ax.annotate(format_str % m, (1.4+i, m), color="black", ha='center')
                text.set_rotation(270)
        Fig.ax.set_xticklabels(luse_cat)
        if label is None: label = var
        Fig.ax.set_ylabel(label) #("%s in %s" % (getattr(X, var).name, getattr(X, var)._units))


# Short Fig version, works for corny
class Fig:
    fig = None # fig object given by pdfpages
    ax = None  # current single axis
    time_format = '%Y'
    layout = (1,1)
    axi = 1
    submode = False

    def __init__(self, fig=None, title='', layout=(1,1), xlabel='', ylabel='',
                size=(11.69,8.27), ylim=None, time_series=True, proj=None,
                savefile=None, time_format='b\nY'):

        # Single PDF page when fig is provided
        if not fig is None:
            Fig.fig = fig
            plt.figure(figsize=size)
            Fig.layout = layout
            Fig.axi = 0
        else:
            pass
            #Fig.fig, Fig.ax = plt.subplots()

        self.savefile = savefile

        if layout != (1,1):
            # For complex layout, do not do anything, just wait for next "with Fig()"
            Fig.submode = True
        else:
            Fig.axi += 1
            if Fig.layout[0]==1 and Fig.layout[1]==1: Fig.axi = 1
            Fig.ax = plt.subplot(Fig.layout[0], Fig.layout[1], Fig.axi, projection=proj)

            plt.title(title)
            Fig.ax.set(xlabel=xlabel, ylabel=ylabel)
            if not ylim is None: Fig.ax.set_ylim(ylim)
            for a in ("top", "right"):
                Fig.ax.spines[a].set_visible(False)
                Fig.ax.get_xaxis().tick_bottom()
                Fig.ax.get_yaxis().tick_left()
            Fig.ax.grid(b=True, alpha=0.4)
            Fig.time_format = time_format
            time_format = re.sub(r'(\w)', r'%\1', Fig.time_format)
            if time_series:
                Fig.ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter(time_format.replace('\\','')))
                plt.tick_params(labelsize=9)

    # Entering `with` statement
    def __enter__(self):
        return(Fig.ax) # makes possibe: with Fig() as ax: ax.change

    # Exiting `with` statement
    def __exit__(self, type, value, traceback):
        # deactivate submode if axis counter exceeds layout shape
        if Fig.submode:
            if Fig.axi == Fig.layout[0]*Fig.layout[1]:
                Fig.submode = False
        elif self.savefile:
            # Save and close single plot
            plt.savefig(self.savefile, bbox_inches='tight', frameon=False, dpi=250)
            plt.close()
        elif Fig.fig:
            # save and close PDF page
            Fig.fig.savefig(bbox_inches='tight')
            plt.close()

# Full Fig version, should be merged with above
class Fig_old:
    fig = None
    axes = []  # 2D array of axes
    ax = None  # current single axis
    axi = None # flat counter for Fig.axes[axi] === ax
    legend = 1
    time_format = '%b %d'
    leftbot_axes = True
    #grid = True
    #layout = (1,1)
    #sharex = True
    #sharey = False
    submode = False
    axcount = 0
    #style = '.-'
    args = {'style':'.-', 'legend': 1, 'grid':True, 'layout':(1,1), 'sharex':True, 'sharey':False, 'proj':False}


    # This is a fake instance, this class always acts with static methods and attributes
    def __init__(self, title='', layout=(1,1), **kwargs):
        # Magic recognition of Fig((1,2),'title')
        if isinstance(title, tuple):
            layout, title = title, layout
            if not isinstance(title, str): title = ''

        # If sub figures are expected
        #print(Fig.submode)
        if Fig.submode:
            Fig.sub(title, **kwargs)
        else:
            Fig.new(title, layout=layout, **kwargs)

    # Entering `with` statement
    def __enter__(self):
        return(Fig.ax) # makes possibe: with Fig() as ax: ax.change

    # Exiting `with` statement
    def __exit__(self, type, value, traceback):

        # hide redundant y and x bars
        if Fig.args['sharex'] and Fig.axes.shape[0] > 1:
            plt.setp([a.get_xticklabels() for a in Fig.axes[0, :]], visible=False)
        if Fig.args['sharey']:
            plt.setp([a.get_yticklabels() for a in Fig.axes[:, 1]], visible=False)

        # make suptitle arrange nicely
        if Fig.args['tight']:
            Fig.fig.tight_layout()
        if Fig.args['layout'] != (1,1):
            Fig.fig.subplots_adjust(top=0.88)

        if Fig.axi >= Fig.axcount-1: # Fig.fig.axes can be actually larger if colorbars were added
            Fig.submode = False

        # Make legend without border
        if Fig.args['legend']:
            try:
                Fig.ax.legend(loc=int(Fig.args['legend'])).get_frame().set_linewidth(0.0)
            except:
                pass

        #Fig.fig.show()


    # Redirect Fig.x to Fig.fig.x
    def __getattr__(self, name):
        try:
            return(getattr(Fig.fig, name))
        except:
            raise AttributeError('Sorry, neither Fig nor Fig.fig have such attribute.')


    @staticmethod
    def new(title='', time_format=None, layout=None, size=(12,4), leftbot_axes=None,
            legend=None, grid=None, sharex=None, sharey=None, ylim=None, xlim=None,
            proj=None, tight=True, time_series=True, **kwargs):

        if layout is None: layout = Fig.args['layout']; Fig.args['layout'] = layout
        if sharex is None: sharex = Fig.args['sharex']; Fig.args['sharex'] = sharex
        if sharey is None: sharey = Fig.args['sharey']; Fig.args['sharey'] = sharey
        Fig.args['legend'] = legend
        Fig.args['grid'] = grid
        Fig.args['tight'] = tight
        Fig.args['time_series'] = time_series

        subplot_dict = {}
        if proj=='cartopy':
            subplot_dict['projection'] = cartopy.crs.PlateCarree()
            Fig.args['proj'] = True
            Fig.args['tight'] = False

        Fig.fig, Fig.axes = plt.subplots(layout[0],layout[1], figsize=size, squeeze=False, subplot_kw=subplot_dict)
        Fig.axcount = len(Fig.fig.axes)
        Fig.axi = -1

        if layout == (1,1):
            Fig.sub(title, time_format=time_format, leftbot_axes=leftbot_axes, legend=legend, grid=grid, xlim=xlim, ylim=ylim, tight=tight, time_series=time_series, **kwargs)
        else:
            Fig.submode = True
            plt.suptitle(title, fontweight='normal')

        return(Fig)


    @staticmethod
    def sub(title='', time_format=None, leftbot_axes=None,
            legend=None, grid=None, xlim=None, ylim=None,
            proj=None, tight=None, time_series=None, **kwargs):
        # Defaults
        if time_format  is None: time_format = Fig.time_format
        if leftbot_axes is None: leftbot_axes = Fig.leftbot_axes
        if legend       is None: legend = Fig.args['legend']
        if grid         is None: grid = Fig.args['grid']
        if tight         is None: tight = Fig.args['tight']
        if time_series  is None: time_series = Fig.args['time_series']


        # New axis
        #Fig.fig, Fig.axes = plt.subplots(layout[0],layout[1], squeeze=False)
        Fig.axi += 1
        print('Axes', str(len(Fig.fig.axes)), 'axi', Fig.axi)
        Fig.ax = Fig.fig.axes[Fig.axi]
        plt.sca(Fig.ax)

        if not ylim is None: Fig.ax.set_ylim(ylim)
        if not xlim is None: Fig.ax.set_xlim(xlim)

        xlabel = 'x'
        xlabel = 'y'
        if 'xlabel' in kwargs: xlabel = kwargs.get('xlabel')
        if 'ylabel' in kwargs: ylabel = kwargs.get('ylabel')
        Fig.ax.set(xlabel=xlabel, ylabel=ylabel)

        if time_series:
            Fig.ax.xaxis_date() # treat x axis as date (fixes some bugs)
        Fig.ax.grid(b=grid, color='black', alpha=0.3)
        Fig.ax.set_title(title, fontweight='bold')

        if leftbot_axes:
            for a in ("top", "right"):
                #for i in len(range(Fig.ax.size)):
                Fig.ax.spines[a].set_visible(False)
                Fig.ax.get_xaxis().tick_bottom()
                Fig.ax.get_yaxis().tick_left()

        # Time Format
        if time_series:
            time_format = interpret_time_format(time_format)
            Fig.ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter(time_format))

        # Legend
        #if not legend:
        #Fig.args['legend'] = False
        #if legend >= 0:
        #    Fig.args['legend'] = int(legend)

        return(Fig.ax)


    @staticmethod
    def save(file='plots/test.pdf', dpi=300, tight=False, overwrite=True, **kwargs):
        # make layout tight to arrange margins
        if tight: Fig.fig.tight_layout()

        # Create folder
        folder = os.path.dirname(os.path.abspath(file))
        if not os.path.exists(folder):
            os.makedirs(folder)
            print('Note: Folders were created:', folder)

        # Number files to avoid overwriting
        if not overwrite and os.path.exists(file):
            i = 0
            file_path, file_ext = os.path.splitext(file)
            while os.path.exists('{}-{:d}{}'.format(file_path, i, file_ext)):
                i += 1
            file = '{}-{:d}{}'.format(file_path, i, file_ext)

        # Savefig
        Fig.fig.savefig(file, dpi=dpi, **kwargs)

        # Print size
        size = "%.1f KB" % (os.path.getsize(file)/1024)
        print('Saved "'+file+'" ('+size+')')


def map(data, var="N", center=None, zoom=17, tiles='openstreetmap', colormap='Spectral', collim=None,
        size=4.5, features=['points','shadow','border','gleam'], luse=False, shadow_factor=1.75, border_factor=1.25,
        usemap=None):

    luse_cat=['urban', 'agriculture', 'wetland', 'forest', 'water']
    luse_col=['red', 'orange', 'lightblue', 'green', 'blue']

    import folium
    #if data is None:
    data = data.dropna(subset=[var])
    #data = data.dropna()
    if center is None:
        center = [data.lat.mean(), data.lon.mean()]
        #[51.352042, 12.431250]
    if collim is None:
        xmin = np.min(data.loc[:,var])
        xmax = np.max(data.loc[:,var])
    else:
        xmin = collim[0]
        xmax = collim[1]

    #data['color'] = ''
    data.loc[:,'color'] = ''

    if luse:
        for i in range(len(luse_cat)):
            data.loc[data.luse_str==luse_cat[i], "color"] = luse_col[i]
        #data['color'] = self.luse_col[self.luse_cat.index(data['luse_str'])] #self.luse_col[data['luse']//100]
    else:
        cmap = matplotlib.cm.get_cmap(colormap)
        for i, row in data.iterrows():
            tmp = (data.at[i,var]-xmin)/(xmax-xmin)
            data.at[i,'color'] = matplotlib.colors.rgb2hex(cmap(tmp)[:3])

    if usemap is None:
        M = folium.Map(location=center, zoom_start=zoom, tiles=tiles)
    else:
        M = usemap

    if any(f in ['border','shadow'] for f in features):
        for i, row in data.iterrows():
            if 'shadow' in features:
                folium.Circle(location=[row["lat"], row["lon"]], radius=size*shadow_factor, color=None, fill_color="black", fill_opacity=0.2).add_to(M)
            if 'border' in features:
                folium.Circle(location=[row["lat"], row["lon"]], radius=size*border_factor, color=None, fill_color="black", fill_opacity=1).add_to(M)

    if any(f in ['points'] for f in features):
        for i, row in data.iterrows():
            folium.Circle(location=[row["lat"], row["lon"]], radius=size, color=None, fill_color=row["color"], fill_opacity=1).add_to(M)
            if 'gleam' in features:
                folium.Circle(location=[row["lat"]+0.00001*size/3, row["lon"]+0.00001*size/3], radius=size/2, color=None, fill_color="white", fill_opacity=0.4).add_to(M)

    if 'lines' in features:
        folium.PolyLine(list(data.loc[:,["lat","lon"]].itertuples(index=False, name=None)), color="black", weight=1, opacity=1).add_to(M)

    return(M)



def xyplot(x, y, z, resolution = 20, vrange = (0,0.5), contour_levels = np.arange(0.05,0.525,0.025), padding=0.05, colorbar=True,
            varlabel="vol. soil moisture (in m$^3$/m$^3$)", maptitle='Map', size=10, xlabel='Easting (in m)', ylabel='Northing (in m)'):
    x = x.values - x.min()
    y = y.values - y.min()
    z = z.values
    xrange = x.max()-x.min()
    yrange = y.max()-y.min()
    xpad = padding*xrange
    ypad = padding*yrange

    mysize = (size,size/xrange*yrange)
    if mysize[1] > size*2:
        mysize = (size*xrange/yrange,size)

    with Fig(title=maptitle, xlabel=xlabel, ylabel=ylabel, size=mysize, time_series=False) as ax:
        q = ax.scatter( x, y, c=z, cmap='Spectral', vmin=vrange[0], vmax=vrange[1])
        ax.set_aspect(1)
        ax.set_xlim(x.min()-xpad,x.max()+xpad)
        ax.set_ylim(y.min()-ypad,y.max()+ypad)
        if colorbar:
            cb = plt.colorbar(q, extend="both", ax=ax, shrink=0.6, pad=0.03, aspect=30)
            cb.set_label(varlabel, rotation=270, labelpad=20)
        plt.grid(color='black', alpha=0.2)


# Cosmetics
# Curved Text
#from functions import *
from matplotlib import patches
from matplotlib import text as mtext

class CurvedText(mtext.Text):
    """
    A text object that follows an arbitrary curve.
    From: https://stackoverflow.com/questions/19353576/curved-text-rendering-in-matplotlib
    """
    def __init__(self, x, y, text, axes, **kwargs):
        super(CurvedText, self).__init__(x[0],y[0],' ', **kwargs)
        axes.add_artist(self)

        # saving the curve:
        self.__x = x
        self.__y = y
        self.__zorder = self.get_zorder()

        # creating the text objects
        self.__Characters = []
        for c in text:
            if c == ' ':
                # make this an invisible 'a':
                t = mtext.Text(0,0,'a')
                t.set_alpha(0.0)
            else:
                t = mtext.Text(0,0,c, **kwargs)

            # resetting unnecessary arguments
            t.set_ha('center')
            t.set_rotation(0)
            t.set_zorder(self.__zorder +1)
            self.__Characters.append((c,t))
            axes.add_artist(t)


    ##overloading some member functions, to assure correct functionality
    ##on update
    def set_zorder(self, zorder):
        super(CurvedText, self).set_zorder(zorder)
        self.__zorder = self.get_zorder()
        for c,t in self.__Characters:
            t.set_zorder(self.__zorder+1)

    def draw(self, renderer, *args, **kwargs):
        """
        Overload of the Text.draw() function. Do not do
        do any drawing, but update the positions and rotation
        angles of self.__Characters.
        """
        self.update_positions(renderer)

    def update_positions(self,renderer):
        """
        Update positions and rotations of the individual text elements.
        """

        #preparations

        ##determining the aspect ratio:
        ##from https://stackoverflow.com/a/42014041/2454357

        ##data limits
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        ## Axis size on figure
        figW, figH = self.axes.get_figure().get_size_inches()
        ## Ratio of display units
        _, _, w, h = self.axes.get_position().bounds
        ##final aspect ratio
        aspect = ((figW * w)/(figH * h))*(ylim[1]-ylim[0])/(xlim[1]-xlim[0])

        #points of the curve in figure coordinates:
        x_fig,y_fig = (
            np.array(l) for l in zip(*self.axes.transData.transform([
            (i,j) for i,j in zip(self.__x,self.__y)
            ]))
        )

        #point distances in figure coordinates
        x_fig_dist = (x_fig[1:]-x_fig[:-1])
        y_fig_dist = (y_fig[1:]-y_fig[:-1])
        r_fig_dist = np.sqrt(x_fig_dist**2+y_fig_dist**2)

        #arc length in figure coordinates
        l_fig = np.insert(np.cumsum(r_fig_dist),0,0)

        #angles in figure coordinates
        rads = np.arctan2((y_fig[1:] - y_fig[:-1]),(x_fig[1:] - x_fig[:-1]))
        degs = np.rad2deg(rads)


        rel_pos = 10
        for c,t in self.__Characters:
            #finding the width of c:
            t.set_rotation(0)
            t.set_va('center')
            bbox1  = t.get_window_extent(renderer=renderer)
            w = bbox1.width
            h = bbox1.height

            #ignore all letters that don't fit:
            if rel_pos+w/2 > l_fig[-1]:
                t.set_alpha(0.0)
                rel_pos += w
                continue

            elif c != ' ':
                t.set_alpha(1.0)

            #finding the two data points between which the horizontal
            #center point of the character will be situated
            #left and right indices:
            il = np.where(rel_pos+w/2 >= l_fig)[0][-1]
            ir = np.where(rel_pos+w/2 <= l_fig)[0][0]

            #if we exactly hit a data point:
            if ir == il:
                ir += 1

            #how much of the letter width was needed to find il:
            used = l_fig[il]-rel_pos
            rel_pos = l_fig[il]

            #relative distance between il and ir where the center
            #of the character will be
            fraction = (w/2-used)/r_fig_dist[il]

            ##setting the character position in data coordinates:
            ##interpolate between the two points:
            x = self.__x[il]+fraction*(self.__x[ir]-self.__x[il])
            y = self.__y[il]+fraction*(self.__y[ir]-self.__y[il])

            #getting the offset when setting correct vertical alignment
            #in data coordinates
            t.set_va(self.get_va())
            bbox2  = t.get_window_extent(renderer=renderer)

            bbox1d = self.axes.transData.inverted().transform(bbox1)
            bbox2d = self.axes.transData.inverted().transform(bbox2)
            dr = np.array(bbox2d[0]-bbox1d[0])

            #the rotation/stretch matrix
            rad = rads[il]
            rot_mat = np.array([
                [cos(rad), sin(rad)*aspect],
                [-sin(rad)/aspect, cos(rad)]
            ])

            ##computing the offset vector of the rotated character
            drp = np.dot(dr,rot_mat)

            #setting final position and rotation:
            t.set_position(np.array([x,y])+drp)
            t.set_rotation(degs[il])

            t.set_va('center')
            t.set_ha('center')

            #updating rel_pos to right edge of character
            rel_pos += w-used


# Plot points with OSM map
# based on https://makersportal.com/blog/2020/4/24/geographic-visualizations-in-python-with-cartopy


def image_spoof(self, tile): # this function pretends not to be a Python script
    url = self._image_url(tile) # get the url of the street map API
    req = Request(url) # start request
    req.add_header('User-agent','Anaconda 3') # add user agent to request
    fh = urlopen(req)
    im_data = io.BytesIO(fh.read()) # get image
    fh.close() # close url
    img = Image.open(im_data) # open image with PIL
    img = img.convert(self.desired_tile_form) # set image format
    return img, self.tileextent(tile), 'lower' # reformat for cartopy


def plot_with_tiles(lons, lats, v, tiles='OSM'):
    if tiles=='OSM':
        cimgt.OSM.get_image = image_spoof # reformat web request for street map spoofing
        osm_img = cimgt.OSM() # spoofed, downloaded street map
    elif tiles=='Satellite':
        cimgt.QuadtreeTiles.get_image = image_spoof # reformat web request for street map spoofing
        osm_img = cimgt.QuadtreeTiles() # spoofed, downloaded street map
    else:
        exit()
    return(osm_img)

#    lonpad = 0.1*(lons.max()-lons.min())
#    latpad = 0.1*(lats.max()-lats.min())
#    zoom = 18-int(3*(lons.max()-lons.min())) # 0->18, 0.5->16, 1->14
#    print(zoom)

#    fig = plt.subplots(figsize=(10,10)) #/xrange*yrange))
#    ax = plt.axes(projection=ccrs.PlateCarree())
#    q = ax.scatter( lons, lats, c=v, cmap='Spectral', vmin=0.1, vmax=0.5, transform=ccrs.PlateCarree())
#    ax.set_xlim(lons.min()-lonpad, lons.max()+lonpad)
#    ax.set_ylim(lats.min()-latpad, lats.max()+latpad)
#    ax.set_title('Soil Moisture')
    #ax.set_extent([x.min()-xpad,x.max()+xpad,y.min()-ypad,y.max()+ypad])
#    ax.add_image(osm_img, zoom)
#    cb = plt.colorbar(q, extend="both", ax=ax, shrink=0.6, pad=0.03, aspect=30)
#    cb.set_label("vol. soil moisture (in m$^3$/m$^3$)", rotation=270, labelpad=20)


############# KML


# Save data as KML
def save_KML(data, var, lat, lon, alt=None, file='test', format_str="%.0f%%", collim=None, cmap='Spectral_r'):

    data.loc[data[lat]==0.0, lat] = np.nan
    data.loc[data[lon]==0.0, lon] = np.nan
    data = data.dropna(subset=[var, lon, lat])

    if collim is None:
        xmin = np.min(data.loc[:,var])
        xmax = np.max(data.loc[:,var])
    else:
        xmin = float(collim[0])
        xmax = float(collim[1])
    #debug()
    data['color'] = None
    #data.loc[:,'color'] = None
    cmap = matplotlib.cm.get_cmap(cmap)
    if xmin < xmax:
        for i, row in data.iterrows():
            tmp = (data.at[i,var]-xmin)/(xmax-xmin)
            if isinstance(tmp, np.float64): # solves a rare bug when data.at[i,var] is a pandas series
                data.at[i,'color'] = matplotlib.colors.rgb2hex(cmap(tmp)[:3])
    kml = simplekml.Kml()

    for i, row in data.iterrows():
        label = format_str % row[var] if format_str else ''
        if alt is None:
            pnt = kml.newpoint(name=label, coords=[(row[lon],row[lat])])
        else:
            pnt = kml.newpoint(name=label, coords=[(row[lon],row[lat],row[alt])], altitudemode='absolute', extrude=1)
            # absolute relativeToGround clampToGround # https://simplekml.readthedocs.io/en/latest/constants.html#simplekml.AltitudeMode
        if row['color'] is not None:
            pnt.style.iconstyle.color = row['color'].replace('#','#ff')
        pnt.style.iconstyle.scale = 1
        pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pal2/icon18.png'
        pnt.style.labelstyle.scale = 0.8

    kml.save(file + '.kml')

def terminal_plot(data, **kwargs):
    import uniplot
    dm = data.dropna()
    my = dm.values
    mx = (dm.index - dm.index.min()) / np.timedelta64(1,'h')
    uniplot.plot(my, mx , height=10, **kwargs)

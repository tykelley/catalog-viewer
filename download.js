var data = source.data;
var filetext =  'index,host_id,x,y,z,dist,rvir,mvir,vmax,vpeak,vtan,vr,infall,peri\n';
for (var i = 0; i < data['index'].length; i++) {
    var currRow = [data['index'][i].toString(),
                   data['host_id'][i].toString(),
                   data['x'][i].toString(),
                   data['y'][i].toString(),
                   data['z'][i].toString(),
                   data['dist'][i].toString(),
                   data['rvir'][i].toString(),
                   data['mvir'][i].toString(),
                   data['vmax'][i].toString(),
                   data['vpeak'][i].toString(),
                   data['vtan'][i].toString(),
                   data['vr'][i].toString(),
                   data['infall'][i].toString(),
                   data['peri'][i].toString().concat('\n')];

    var joined = currRow.join();
    filetext = filetext.concat(joined);
}

var filename = fname;
var blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });

//addresses IE
if (navigator.msSaveBlob) {
    navigator.msSaveBlob(blob, filename);
} else {
    var link = document.createElement("a");
    link = document.createElement('a')
    link.href = URL.createObjectURL(blob);
    link.download = filename
    link.target = "_blank";
    link.style.visibility = 'hidden';
    link.dispatchEvent(new MouseEvent('click'))
}
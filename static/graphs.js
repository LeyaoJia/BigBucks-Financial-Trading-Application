var ready = (callback) => {
    if (document.readyState != "loading") callback();
    else document.addEventListener("DOMContentLoaded", callback);
  }
  
  ready(() => { 
    makeplots();
      /* Do things after DOM has fully loaded */ 
  });

var selectedsymbol = document.getElementById("symbol").innerText;


function makeplots(){
  makeplota();
  makeplotb();
  makeplotc();
  makeplotd();
  makeplote();
  makeplotf();
  //makeplotg();
}

function makeplota() {
    console.log("makeplot: start")
    
    // Make an AJAX request to the server-side endpoint to retrieve data from the database
    fetch('/get_hitorical_close_data', {
        method: 'POST',
        body: JSON.stringify({symbol: selectedsymbol}),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        processHistData(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });

    console.log("makeplot: end")
  
};

function makeplotb() {
  console.log("makeplot: start")

  // Make an AJAX request to the server-side endpoint to retrieve data from the database
  fetch('/get_hitorical_return_data', {
      method: 'POST',
      body: JSON.stringify({symbol: selectedsymbol}),
      headers: {
          'Content-Type': 'application/json'
      }
  })
  .then(response => response.json())
  .then(data => {
      processRetData(data);
  })
  .catch(error => {
      console.error('Error:', error);
  });

  console.log("makeplot: end")

};
function makeplotc() {
  console.log("makeplot: start")
  
  // Make an AJAX request to the server-side endpoint to retrieve data from the database
  fetch('/get_return_comparison_data', {
      method: 'POST',
      body: JSON.stringify({symbol: selectedsymbol}),
      headers: {
          'Content-Type': 'application/json'
      }
  })
  .then(response => response.json())
  .then(data => {
      processRetCompareData(data);
  })
  .catch(error => {
      console.error('Error:', error);
  });

  console.log("makeplot: end")

};
function makeplotd() {
  console.log("makeplot: start")
  
  // Make an AJAX request to the server-side endpoint to retrieve data from the database
  fetch('/get_hitorical_return_data', {
      method: 'POST',
      body: JSON.stringify({symbol: selectedsymbol}),
      headers: {
          'Content-Type': 'application/json'
      }
  })
  .then(response => response.json())
  .then(data => {
    processHistogramData(data);
  })
  .catch(error => {
      console.error('Error:', error);
  });

  console.log("makeplot: end")

};

function makeplote() {
  console.log("makeplot: start")
  
  // Make an AJAX request to the server-side endpoint to retrieve data from the database
  fetch('/get_price_movement_data', {
      method: 'POST',
      body: JSON.stringify({symbol: selectedsymbol}),
      headers: {
          'Content-Type': 'application/json'
      }
  })
  .then(response => response.json())
  .then(data => {
    processPriceMoveData(data);
  })
  .catch(error => {
      console.error('Error:', error);
  });

  console.log("makeplot: end")

};

function makeplotf() {
  console.log("makeplot: start")
  
  // Make an AJAX request to the server-side endpoint to retrieve data from the database
  fetch('/get_two_returns_data', {
      method: 'POST',
      body: JSON.stringify({symbol: selectedsymbol}),
      headers: {
          'Content-Type': 'application/json'
      }
  })
  .then(response => response.json())
  .then(data => {
    processTwoReturnsData(data);
  
  })
  .catch(error => {
      console.error('Error:', error);
  });

  console.log("makeplot: end")

};


// the first vis
function processHistData(data) {
  console.log("processData: start")
  let x = [], y = []

  for (let i=0; i<data.length; i++) {
      row = data[i];

      let date = new Date(row['Date']);
      let formattedDate = date.toLocaleDateString('en-US', {year: '2-digit', month: '2-digit', day: '2-digit'});
      
      x.push(formattedDate);
      y.push( row['Close'] );
  } 
  makePlotly( x, y );
  console.log("processData: end")
}

// the second vis
function processRetData(data) {
  console.log("processData: start")
  let x = [], y = []

  for (let i=0; i<data.length; i++) {
      row = data[i];
      let date = new Date(row['Date']);
      let formattedDate = date.toLocaleDateString('en-US', {year: '2-digit', month: '2-digit', day: '2-digit'});
      
      x.push(formattedDate);
      y.push( row['Return'] );
  } 
  makeScatterPlotb( x, y );
  console.log("processData: end")
}

// the 3rd vis
function processRetCompareData(data) {
  console.log("processData: start")
  let x = [], y = []
  for (let i=0; i<data.length; i++) {
      row = data[i];
      x.push( row['Return(-1)'] );
      y.push( row['Return'] );
  } 
  makeScatterPlotc( x, y );
  console.log("processData: end")
}

// the 4th vis
function processHistogramData(data) {
  console.log("processData: start")
  let x = []

  for (let i=0; i<data.length; i++) {
      row = data[i];
      
      x.push( row['Return'] );
  } 
  makePlotd(x);
  console.log("processData: end")
}

// the 5th vis
function rescale(y) {
  let min_y = Math.min(...y);
  let max_y = Math.max(...y);
  let range = max_y - min_y;
  let rescaled_y = y.map(val => (val - min_y) / range);
  return rescaled_y;
}
function processPriceMoveData(data) {
  console.log("processData: start")
  let x1 = []
  let y1 = []
  let x2 = []
  let y2 = []

  if (!data || !data['target_data'] || !data['spy_data']) {
    console.error('Invalid data format')
    return
  }

  for (let i=0; i<data['target_data'].length; i++) {
    let row = data['target_data'][i];

    let date = new Date(row['date']);
    let formattedDate = date.toLocaleDateString('en-US', {year: '2-digit', month: '2-digit', day: '2-digit'});
    
    x1.push(formattedDate);
    y1.push(row['close']);
  }
  for (let i=0; i<data['spy_data'].length; i++) {
    let row = data['spy_data'][i];
    
    let date = new Date(row['date']);
    let formattedDate = date.toLocaleDateString('en-US', {year: '2-digit', month: '2-digit', day: '2-digit'});
    
    x2.push(formattedDate);
    y2.push(row['close']);
    
  } 
  makePlote(x1, rescale(y1), x2, rescale(y2));
  console.log("processData: end")
}

// the 6th&7th vis
function processTwoReturnsData(data){
  console.log("processData: start")
  let x1 = []
  let y1 = []
  let x2 = []
  let y2 = []

  if (!data || !data['target_data'] || !data['spy_data']) {
    console.error('Invalid data format')
    return
  }

  for (let i=0; i<data['target_data'].length; i++) {
    let row = data['target_data'][i];

    let date = new Date(row['Date']);
    let formattedDate = date.toLocaleDateString('en-US', {year: '2-digit', month: '2-digit', day: '2-digit'});
    
    x1.push(formattedDate);
    y1.push(row['Return']);
    
  }
  for (let i=0; i<data['spy_data'].length; i++) {
    let row = data['spy_data'][i];
    
    let date = new Date(row['Date']);
    let formattedDate = date.toLocaleDateString('en-US', {year: '2-digit', month: '2-digit', day: '2-digit'});
    
    x2.push(formattedDate);
    y2.push(row['Return']);
    
  } 
  makePlotf(x1, y1, x2, y2);
  // as the data for 7th vis was partly the same as that of the 6th, add one drawing function here
  makePlotg(y1, y2);
  console.log("processData: end")

}


function makePlotly( x, y ){
  console.log("makePlotly: start")
  var traces = [{
        x: x,
        y: y
  }];
  var layout  = { 
    title: selectedsymbol+ " Adjusted Close Price History",
    font: {
      size: 10
    },
    xaxis: {
      title: 'Time'
      },
    yaxis: {
      title: 'Close Price'
    }}

  myDiv = document.getElementById('myDiva');
  Plotly.newPlot( myDiv, traces, layout );
  console.log("makePlotly: end")

};

function makeScatterPlotb( x, y ){
  console.log("makePlotly: start")
  var traces = [{
        x: x,
        y: y,
        mode: 'markers',
        type: 'scatter'
  }];
  var layout  = { 
    title: selectedsymbol+ " Simple Return History",
    font: {
      size: 10
    },
    xaxis: {
      title: 'Time'
    }, 
    yaxis: {
      title: 'Return'
    }}

  myDiv = document.getElementById('myDivb');
  Plotly.newPlot( myDiv, traces, layout );
  console.log("makePlotly: end")

};

function makeScatterPlotc( x, y ){
  console.log("makePlotly: start")
  var traces = [{
        x: x,
        y: y,
        mode: 'markers',
        type: 'scatter'
  }];
  var layout  = { 
    title: selectedsymbol+ " Compare Return",
    font: {
      size: 10
    },
    xaxis: {
      title: 'Time'
    }, 
    yaxis: {
      title: 'Return'
    }}
  myDiv = document.getElementById('myDivc');
  Plotly.newPlot( myDiv, traces, layout );
  console.log("makePlotly: end")

};
function makePlotd( x ){
  console.log("makePlotly: start")
  var traces = [{
        x: x,
        type: 'histogram'
  }];
  var layout  = { 
    title: selectedsymbol+ " Histogram Simple Return",
    font: {
      size: 10
    },
    xaxis: {
      title: 'Time'
    }, 
    yaxis: {
      title: 'Return'
    }
  }
  myDiv = document.getElementById('myDivd');
  Plotly.newPlot( myDiv, traces, layout );
  console.log("makePlotly: end")

};


function makePlote( x1, y1, x2, y2 ){
  console.log("makePlotly: start")
  var traces = [{
        x: x1,
        y: y1,
        mode: 'lines',
        name: selectedsymbol
  },
  {
    x: x2,
    y: y2,
    mode: 'lines',
    name: "SPY"
  }
];
  var layout  = { 
    title: "Daily price movements for " + selectedsymbol+ " and SPY",
    font: {
      size: 10
    },
    xaxis: {
      title: selectedsymbol
    }, 
    yaxis: {
      title: 'SPY'
    }
  }

  myDiv = document.getElementById('myDive');
  Plotly.newPlot( myDiv, traces, layout );
  console.log("makePlotly: end")

};

function makePlotf( x1, y1, x2, y2 ){
  console.log("makePlotly: start")
  var traces = [{
        x: x1,
        y: y1,
        mode: 'lines',
        name: selectedsymbol
  },
  {
    x: x2,
    y: y2,
    mode: 'lines',
    name: "SPY"
  }
];
  var layout  = { 
    title: "Daily percentage change in price for " + selectedsymbol+ " and SPY",
    font: {
      size: 10
    },
    xaxis: {
      title: selectedsymbol + 'Price Change'
    }, 
    yaxis: {
      title: 'SPY Price Change'
    }
  }

  myDiv = document.getElementById('myDivf');
  Plotly.newPlot( myDiv, traces, layout );
  console.log("makePlotly: end")

};


function linearRegression(x,y){
  var lr = {};
  var n = y.length;
  var sum_x = 0;
  var sum_y = 0;
  var sum_xy = 0;
  var sum_xx = 0;
  var sum_yy = 0;

  for (var i = 0; i < y.length; i++) {

      sum_x += x[i];
      sum_y += y[i];
      sum_xy += (x[i]*y[i]);
      sum_xx += (x[i]*x[i]);
      sum_yy += (y[i]*y[i]);
  } 

  lr['sl'] = (n * sum_xy - sum_x * sum_y) / (n*sum_xx - sum_x * sum_x);
  lr['off'] = (sum_y - lr.sl * sum_x)/n;
  lr['r2'] = Math.pow((n*sum_xy - sum_x*sum_y)/Math.sqrt((n*sum_xx-sum_x*sum_x)*(n*sum_yy-sum_y*sum_y)),2);

  return lr;
}

function makePlotg( y1, y2 ){
  console.log("makePlotg: start")
  var traces = {
    x: y2,
    y: y1,
    mode: 'markers',
    type: 'scatter',
    name: selectedsymbol + ' versus SPY'
  };

  var lr = linearRegression(y2, y1);
  var fit_from = Math.min(...y2)
  var fit_to = Math.max(...y1)
  var fit = {
    x: [fit_from, fit_to],
    y: [fit_from*lr.sl+lr.off, fit_to*lr.sl+lr.off],
    mode: 'lines',
    name: 'Regression Line'
    // type: 'scatter',
    // name: "R2=".concat((Math.round(lr.r2 * 10000) / 10000).toString())
  };

  var data = [ traces, fit ];
  var layout  = { 
    title: selectedsymbol+ " return versus market return with regression line",
    font: {
      size: 10
    },
    xaxis: {
      title: selectedsymbol + ' Return'
    }, 
    yaxis: {
      title: 'SPY Return'
    }
  }

  myDiv = document.getElementById('myDivg');
  Plotly.newPlot( myDiv, data, layout );
  console.log("makePlotg: end")

};


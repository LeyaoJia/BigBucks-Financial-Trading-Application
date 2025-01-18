var ready = (callback) => {
    if (document.readyState != "loading") callback();
    else document.addEventListener("DOMContentLoaded", callback);
  }
  
  ready(() => { 
    makeploth();
      /* Do things after DOM has fully loaded */ 
  });

  
// the EF graph
function makeploth() {
    console.log("makeplot: start")
    // Make an AJAX request to the server-side endpoint to retrieve data from the database
    fetch('/get_ef_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
      processEFData(data);
  
    })
    .catch(error => {
        console.error('Error:', error);
    });
  
    console.log("makeplot: end")
  }



// the EF vis
function processEFData(data) {
    console.log("processData: start")
    let x = []
    let y = []
  
    for (let i=0; i<data['returns'].length; i++) {
      
      x.push(data['vol'][i]);
      y.push(data['returns'][i]);
      
    }
    let x0 = data['current'][1]
    let y0 = data['current'][0]
  
    makePloth(x, y, x0, y0);


    console.log("processData: end")
  }



  function makePloth(x, y, x0, y0) {

    var curve = {
      x: x,
      y: y,
      mode: 'markers',
      name: 'Efficient Frontier'
    };
  
    var point = {
      x: [x0],
      y: [y0],
      mode: 'markers',
      name: 'current',
      marker : {
        color: 'orange',
        size: 20,
        symbol: "star"
      }
    };
  
    var data = [curve, point];
  
    var layout = {
      title: 'Efficient Frontier',
      font: {
        size: 12
      },
      xaxis: {
        title: 'Portfolio Volatility'
      }, 
      yaxis: {
        title: 'Portfolio Return'
      }
    };
  
    var myDiv = document.getElementById('myDivh');
  
    Plotly.newPlot(myDiv, data, layout);
  }
  
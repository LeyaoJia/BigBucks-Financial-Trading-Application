var ready = (callback) => {
    if (document.readyState != "loading") callback();
    else document.addEventListener("DOMContentLoaded", callback);
  }
  
  ready(() => { 
    makeplot();
      /* Do things after DOM has fully loaded */ 
  });

  function makeplot() {
    console.log("makeplot: start")
    // Make an AJAX request to the server-side endpoint to retrieve data from the database
    fetch('/get_pie_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
      processData(data);
  
    })
    .catch(error => {
        console.error('Error:', error);
    });
  
    console.log("makeplot: end")
  }

  function processData(data) {
    console.log("processData: start")
    let x = []
    let y = []
  
    for (let i=0; i<data.length; i++) {
      row = data[i]
      x.push(row['Symbol']);
      y.push(row['Value']);
    }
  
    makePlotly(x, y);
    console.log("processData: end")
  }

//   function makePlotly( x, y ){
//     console.log("makePlotly: start")
//     var traces = [{
//         values: y,
//         labels: x,
//         type: 'pie'
//       }];

//     var layout = {
//         height: 400,
//         width: 500
//       };
  
//     myDiv = document.getElementById('holding_pie');
//     Plotly.newPlot( myDiv, traces, layout );
//     console.log("makePlotly: end")
  
//   };

  function makePlotly(x, y) {
    console.log("makePlotly: start");
    var colors = ['#e7ecef', '#274c77', '#6096ba', '#a3cef1', '#8b8c89'];
    var traces = [{   values: y,    labels: x,    type: 'pie',    
            marker: {      colors: colors    }
            // texttemplate: "%{percent:.1%}",
          }];
  
    var layout = {
      height: 400,
      width: 400,
      font: {
        color: '#444',
        size: 14
      },
      paper_bgcolor: '#f1f2f4',
      margin: {
        t: 0
      }
    };
  
    myDiv = document.getElementById('holding_pie');
    Plotly.newPlot(myDiv, traces, layout);
    document.body.style.margin = '0';
    console.log("makePlotly: end");
  };
  
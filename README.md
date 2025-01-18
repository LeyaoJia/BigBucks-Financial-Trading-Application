# Contents:
This is a simulated trading platform with user and admin design. 
<br>
<br>
As a **user**, you are initialized 1,000,000 USD when signed in. You can use this "fake money" to buy whatever portfolio you want in real-time stock prices. The platform will keep track of your portfolio in real-time. You can check the **Sharpe ratio**, and **Efficient Frontier** of your portfolio, as well as one price tracking plot and three risk-return plots.
<br>
<br>
As an **admin**, you can monitor the lists of stocks across all users by ticker symbol, name, shares held, and price per share. You can also monitor the List summary of current day's market orders across all users by ticker symbol, name, shares bought, and shares sold.

# UI/UX Design:
Find in code design diagram, component diagram, container diagram, and system context diagram.

# Instructions to use:

1) Please create a config.py file under the "Bigbucks" folder with your api_key inside before starting to use it. If you don't have one, feel free to contact the author too.

* config.py example: api_key = '[your api_key]'

2) When trying to use, first run "flask --app BigBucks init-db" when you're in the "Bigbucks" folder, then run from terminal "flask --app BigBucks --debug run"

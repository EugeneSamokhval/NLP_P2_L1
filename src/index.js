console.log('JS loaded');

const user_input_element = document.getElementsByClassName('InputField')[0];
const send_button = document.getElementById("SendButton");
const output_table_element = document.querySelector('.OutputContainer tbody');

send_button.addEventListener('click', () => {
    fetch('http://localhost:2000/find/?user_input=' + encodeURIComponent(user_input_element.value))
        .then((response) => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then((data) => {
            console.log(data);
            output_table_element.innerHTML = ''; // Clear previous results
            data.forEach(item => {
                const row = output_table_element.insertRow();
                const cell1 = row.insertCell(0);
                const cell2 = row.insertCell(1);
                cell1.textContent = item.file_url;
                cell2.textContent = item.file_url;
            });
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
        });
});

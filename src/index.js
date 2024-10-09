console.log('JS loaded');

const user_input_element = document.getElementsByClassName('InputField')[0];
const send_button = document.getElementById("SendButton");
const output_table_element = document.querySelector('.OutputContainer tbody');
const help_button = document.getElementById('HelpButton')
const pop_up_window = document.getElementById('PopUpWindow')
const close_pop_up_button = document.getElementById('CloseHelpButton')

const server_ip = 'http://192.168.31.32:8000'

function getSurroundingString(str, position) {
    if (position < 0 || position >= str.length) {
        return '';
    }
    console.log(position)

    const start = Math.max(0, position - 50);
    const end = Math.min(str.length, position + 50);

    return str.substring(start, end);
}

send_button.addEventListener('click', () => {   
    fetch(server_ip + '/find/?user_input=' + encodeURIComponent(user_input_element.value))
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then((data) => {
            output_table_element.innerHTML = ''; // Clear previous results
            let iteration = 0;
            data.forEach(item => {
                const row = output_table_element.insertRow();
                const cell1 = row.insertCell(0);
                const cell2 = row.insertCell(1);        
                const cell3 = row.insertCell(2);
                cell1.textContent = item.filename;
                cell2.innerHTML = '<a target="_blank" href='+ 'http://'+ item.file_path + '>' + item.file_path + '</a>';
                cell3.textContent = item.raw_text;
                console.log( cell3.textContent)
                iteration++;
            });
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
});

help_button.addEventListener('click', ()=>{
    pop_up_window.style.display = 'block';
})
close_pop_up_button.addEventListener('click', ()=>{
    pop_up_window.style.display = 'none';
})
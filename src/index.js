console.log('JS loaded');

const user_input_element = document.getElementsByClassName('InputField')[0];
const send_button = document.getElementById("SendButton");
const output_table_element = document.querySelector('.OutputContainer tbody');
const help_button = document.getElementById('HelpButton')
const pop_up_window = document.getElementById('PopUpWindow')

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
    fetch('http://192.168.31.32:8000/find/?user_input=' + encodeURIComponent(user_input_element.value))
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            const urls = data.map(entry => entry.file_path);
            return Promise.all(urls.map(url =>
                fetch('http://' + url).then(response => response.text())
            ))
            .then(files => {
                return {data, files}; // Return both data and files
            });
        })
        .then(({data, files}) => {
            output_table_element.innerHTML = ''; // Clear previous results
            let iteration = 0;
            console.log(files)  
            data.forEach(item => {
                const row = output_table_element.insertRow();
                const cell1 = row.insertCell(0);
                const cell2 = row.insertCell(1);        
                const cell3 = row.insertCell(2);
                cell1.textContent = item.filename;
                cell2.innerHTML = '<a target="_blank" href='+ 'http://'+ item.file_path + '>' + item.file_path + '</a>';
                cell3.textContent = getSurroundingString(files[iteration], item.raw_text[0].pos[0]);
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
pop_up_window.addEventListener('click', ()=>{
    pop_up_window.style.display = 'none';
})
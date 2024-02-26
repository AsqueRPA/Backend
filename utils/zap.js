import axios from 'axios';

async function createGoogleSheet(data) {
    try {
        const response = await axios.post('https://hooks.zapier.com/hooks/catch/17339037/3ecjqrn/', data);
        console.log(response.data);
        return response.data;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

async function updateGooleSheet(data) {
    try {
        const response = await axios.post('https://hooks.zapier.com/hooks/catch/17339037/3ejmdrj/', data);
        console.log(response.data);
        return response.data;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

export default {createGoogleSheet, updateGooleSheet};

const data = { 'sheetUrl': 'https://docs.google.com/spreadsheets/d/1-AGOrQohIbBhYXs0Aw9h2jJi1YN2K0PpJuHf79cU67Q/edit#gid=0', 'name': 'dyllan', 'linkedinUrl': 'linkedin.com', 'response': 'thanks'};
// // Call your function with sample data or replace it with actual data
updateGooleSheet(data).then(console.log).catch(console.error);
 
// If you intend to use this function in another file, uncomment the line below
// module.exports = makeZapRequest;

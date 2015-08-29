import Alt from 'alt';

const alt = new Alt();

alt.dispatcher.register(::console.log);

export default alt;

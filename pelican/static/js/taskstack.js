/* jshint esversion: 6 */
document.addEventListener('DOMContentLoaded', function() {
    function updateActiveProgressBars() {
	const pomodoros = document.querySelectorAll('.worked.active');

	pomodoros.forEach(pomodoro => {
	    const startTime = pomodoro.dataset.start;
	    const pomodoroDuration = pomodoro.dataset.unit;
	    const pomodoroGrace = pomodoro.dataset.grace;
	    const now = Date.now();
	    const currentTime = Math.floor(now / 1000);
	    const duration = Math.ceil((currentTime - startTime) / 60);
	    const progress =  Math.max(0, Math.min(100, (duration / pomodoroDuration) * 100));
	    const progressBar = pomodoro.querySelector('.progress-bar');
	    progressBar.style.setProperty('--progress', progress + '%');
	    progressBar.dataset.progress = progress;
	    if( duration > (pomodoroDuration + pomodoroGrace) ) {
		progressBar.classList.add('overflow');
	    }
	    const progressLabel = pomodoro.querySelector('.progress-bar .progress .progress-label');
	    progressLabel.innerText = duration;
	    const endLabel = pomodoro.querySelector('.end');
	    endLabel.innerText = (now.getUTCHours() < 10?'0':'') + now.getUTCHours() + ':' + (now.getUTCMinutes() < 10?'0':'') + now.getUTCMinutes();
	    endLabel.title = now.getUTCFullYear() + '-' + ((now.getUTCMonth() < 9)?'0':'') + (now.getUTCMonth() + 1) + '-' + ((now.getUTCDate()<10)?'0':'') + now.getUTCDate();
	    setTimeout(window.updateActiveProgressBars, 15000);
	});
    }

    window.updateActiveProgressBars = updateActiveProgressBars;
    updateActiveProgressBars();
});

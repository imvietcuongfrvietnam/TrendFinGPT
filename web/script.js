// script.js
document.addEventListener('DOMContentLoaded', function() {
    const startDateInput = document.getElementById('startDate');
    const loadTrendsButton = document.getElementById('loadTrendsButton');
    const trendsContainer = document.getElementById('trends-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessageElement = document.getElementById('error-message');

    // Thiết lập ngày mặc định là hôm nay
    const today = new Date();
    const yearToday = today.getFullYear();
    const monthToday = String(today.getMonth() + 1).padStart(2, '0');
    const dayToday = String(today.getDate()).padStart(2, '0');
    startDateInput.value = `${yearToday}-${monthToday}-${dayToday}`;

    loadTrendsButton.addEventListener('click', loadAndDisplayTrends);

    // Hàm tạo màu ngẫu nhiên cho word cloud
    function getRandomWordCloudColor() {
        const h = Math.floor(Math.random() * 360);
        const s = 60 + Math.floor(Math.random() * 31); // Saturation 60-90%
        const l = 40 + Math.floor(Math.random() * 21); // Lightness 40-60% (màu đậm, dễ đọc)
        return `hsl(${h}, ${s}%, ${l}%)`;
    }
    
    // Lưu trữ các interval ID để có thể xóa khi hover ra ngoài hoặc tải lại
    // Sử dụng Map để lưu trữ interval cho từng container
    const activeWordCloudIntervals = new Map();


    async function loadAndDisplayTrends() {
        const startDateString = startDateInput.value;
        if (!startDateString) {
            showError("Vui lòng chọn ngày bắt đầu.");
            return;
        }

        showLoading(true);
        clearError();
        trendsContainer.innerHTML = ''; 

        // Xóa tất cả các interval đang chạy trước đó
        activeWordCloudIntervals.forEach(intervalId => clearInterval(intervalId));
        activeWordCloudIntervals.clear();


        const startDate = new Date(startDateString);
        const numberOfDaysToDisplay = 7;
        let filesFetched = 0;
        let filesSuccessfullyParsed = 0;
        let daysWithDataDisplayed = 0;

        console.log(`Bắt đầu tải trends từ: ${startDateString} cho ${numberOfDaysToDisplay} ngày.`);

        for (let i = 0; i < numberOfDaysToDisplay; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);

            const generationDate = new Date(currentDate);
            generationDate.setDate(currentDate.getDate() - 1); 
            
            const year = generationDate.getFullYear();
            const month = String(generationDate.getMonth() + 1).padStart(2, '0');
            const day = String(generationDate.getDate()).padStart(2, '0');
            
            const predictionGeneratedDateStr = `${year}-${month}-${day}`;
            // Đảm bảo đường dẫn này đúng với cách bạn chạy web server
            // Nếu index.html và output/ nằm cùng cấp, thì chỉ cần 'output/...'
            const filePath = `../output/${predictionGeneratedDateStr}/predicted_trends_${year}${month}${day}.json`;

            try {
                const response = await fetch(filePath);
                filesFetched++;
                if (!response.ok) {
                    console.warn(`Không tìm thấy file: ${filePath} (HTTP ${response.status})`);
                    if (i < 5) { 
                        displayNoDataForDay(currentDate.toISOString().split('T')[0], "Không có dữ liệu dự đoán.");
                    }
                    continue; 
                }
                const predictionsData = await response.json();
                filesSuccessfullyParsed++;

                const targetDateStr = currentDate.toISOString().split('T')[0];
                const trendsForCurrentDate = predictionsData.filter(p => p.target_forecast_date === targetDateStr);
                
                if (trendsForCurrentDate && trendsForCurrentDate.length > 0) {
                    displayDayCard(targetDateStr, trendsForCurrentDate);
                    daysWithDataDisplayed++;
                } else {
                    if (i < 5) {
                         displayNoDataForDay(targetDateStr, "Không có dự đoán cụ thể cho ngày này trong file.");
                    }
                }

            } catch (error) {
                console.error(`Lỗi khi tải hoặc xử lý file ${filePath}:`, error);
                 if (i < 5) {
                    displayNoDataForDay(currentDate.toISOString().split('T')[0], `Lỗi tải dữ liệu.`);
                 }
            }
        }
        showLoading(false);
        if (daysWithDataDisplayed === 0) {
            // ... (logic hiển thị lỗi giữ nguyên) ...
            if (filesFetched > 0 && filesSuccessfullyParsed === 0) {
                showError("Đã tải được một số file nhưng không thể phân tích nội dung JSON. Kiểm tra định dạng file JSON và console.");
            } else if (filesFetched === 0) {
                showError("Không tìm thấy bất kỳ file dự đoán nào cho khoảng thời gian đã chọn. Hãy đảm bảo pipeline Python đã chạy và tạo output đúng cấu trúc.");
            } else {
                showError("Không có dữ liệu trend nào được hiển thị. Có thể các file JSON không chứa dự đoán cho các ngày đã chọn.");
            }
        }
    }

    function formatKeywordForDisplay(keywordStr) {
        if (typeof keywordStr !== 'string') return keywordStr;
        let formattedStr = keywordStr.replace(/_/g, " ");
        return formattedStr.split(' ')
                           .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                           .join(' ');
    }
    
    function displayDayCard(dateStr, trends) {
        const dayDiv = document.createElement('div');
        dayDiv.classList.add('day-prediction');

        const title = document.createElement('h3');
        title.textContent = `Dự đoán cho: ${dateStr}`;
        dayDiv.appendChild(title);

        const wordcloudCanvasContainer = document.createElement('div');
        wordcloudCanvasContainer.classList.add('wordcloud-canvas-container');
        // Gán một ID duy nhất cho container để quản lý interval
        const containerId = `wc-container-${dateStr}`;
        wordcloudCanvasContainer.id = containerId;
        dayDiv.appendChild(wordcloudCanvasContainer);
        
        const ul = document.createElement('ul');
        trends.sort((a, b) => a.rank - b.rank).slice(0, 5).forEach(trend => {
            const li = document.createElement('li');
            const rankSpan = document.createElement('span');
            rankSpan.classList.add('keyword-rank');
            rankSpan.textContent = `${trend.rank}.`;
            const keywordSpan = document.createElement('span');
            keywordSpan.classList.add('keyword');
            keywordSpan.textContent = formatKeywordForDisplay(trend.keyword);
            const scoreSpan = document.createElement('span');
            scoreSpan.classList.add('score');
            scoreSpan.textContent = `${Number(trend.predicted_score_for_target_date).toFixed(2)}`;
            li.appendChild(rankSpan);
            li.appendChild(keywordSpan);
            li.appendChild(scoreSpan);
            ul.appendChild(li);
        });
        dayDiv.appendChild(ul);
        trendsContainer.appendChild(dayDiv); 

        const wordcloudListData = trends.map(item => {
            const displayKeyword = formatKeywordForDisplay(item.keyword);
            let score = parseFloat(item.predicted_score_for_target_date || item.base_trend_score || item.score || 10);
            if (isNaN(score) || score <= 0) score = 10; 
            return [displayKeyword, score]; 
        }).slice(0, 30);

        if (wordcloudListData.length > 0 && typeof WordCloud !== 'undefined') {
            const baseWordcloudOptions = {
                list: wordcloudListData,
                gridSize: Math.round(16 * wordcloudCanvasContainer.offsetWidth / 1024) || 10, // Tăng gridSize mặc định một chút
                weightFactor: function(size) { return Math.log(size + 1) * 8 + 3; }, // Tinh chỉnh weightFactor
                fontFamily: 'Verdana, Geneva, sans-serif', // Thử font khác
                color: 'random-dark', // Màu ban đầu
                backgroundColor: '#ffffff00',
                rotateRatio: 0.35,
                minRotation: -Math.PI / 5, 
                maxRotation: Math.PI / 5,
                shuffle: true, // Shuffle cho mỗi lần vẽ lại để có hiệu ứng động hơn
                shape: 'circle', 
                minSize: 6, 
                drawOutOfBound: false,
                ellipticity: 0.6
            };

            // Hàm để vẽ/vẽ lại word cloud với màu động
            function drawAnimatedWordCloud(container, options) {
                try {
                    const dynamicOptions = { ...options, color: getRandomWordCloudColor };
                    WordCloud(container, dynamicOptions);
                } catch (wcError) {
                    console.error(`WordCloud rendering error for ${dateStr}:`, wcError);
                    container.textContent = "Lỗi vẽ WordCloud.";
                }
            }

            // Vẽ lần đầu với màu ngẫu nhiên
            drawAnimatedWordCloud(wordcloudCanvasContainer, baseWordcloudOptions);
            
            // Kích hoạt hiệu ứng "nhấp nháy" màu khi hover
            dayDiv.addEventListener('mouseenter', () => {
                // Xóa interval cũ cho container này nếu có
                if (activeWordCloudIntervals.has(containerId)) {
                    clearInterval(activeWordCloudIntervals.get(containerId));
                }
                // Vẽ lại ngay khi hover để có màu mới
                drawAnimatedWordCloud(wordcloudCanvasContainer, baseWordcloudOptions); 
                // Bắt đầu interval mới
                const intervalId = setInterval(() => {
                    if (document.body.contains(wordcloudCanvasContainer)) {
                        drawAnimatedWordCloud(wordcloudCanvasContainer, baseWordcloudOptions);
                    } else {
                        clearInterval(intervalId); // Dừng nếu element không còn
                        activeWordCloudIntervals.delete(containerId);
                    }
                }, 1200); // Thời gian nhấp nháy (mili giây)
                activeWordCloudIntervals.set(containerId, intervalId);
            });

            dayDiv.addEventListener('mouseleave', () => {
                if (activeWordCloudIntervals.has(containerId)) {
                    clearInterval(activeWordCloudIntervals.get(containerId));
                    activeWordCloudIntervals.delete(containerId);
                    // Tùy chọn: Vẽ lại một lần với màu cố định khi chuột rời đi
                    // WordCloud(wordcloudCanvasContainer, { ...baseWordcloudOptions, color: 'random-dark', shuffle: false });
                }
            });

        } else if (typeof WordCloud === 'undefined') {
            console.error("WordCloud library is not loaded!");
            wordcloudCanvasContainer.textContent = "Lỗi thư viện WordCloud."
        } else {
             wordcloudCanvasContainer.textContent = "Không đủ dữ liệu cho WordCloud."
        }
    }
    
    function displayNoDataForDay(dateStr, message = "Không có dữ liệu.") {
        // ... (Hàm này giữ nguyên) ...
        const dayDiv = document.createElement('div');
        dayDiv.classList.add('day-prediction');
        const title = document.createElement('h3');
        title.textContent = `Dự đoán cho ngày: ${dateStr}`;
        dayDiv.appendChild(title);
        
        const wordcloudPlaceholder = document.createElement('div');
        wordcloudPlaceholder.classList.add('wordcloud-canvas-container');
        wordcloudPlaceholder.textContent = "N/A";
        dayDiv.appendChild(wordcloudPlaceholder);

        const p = document.createElement('p');
        p.textContent = message;
        dayDiv.appendChild(p);
        trendsContainer.appendChild(dayDiv);
    }

    function showLoading(isLoading) {
        loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }
    function showError(message) {
        errorMessageElement.textContent = message;
        errorMessageElement.style.display = message ? 'block' : 'none';
    }
    function clearError() {
        errorMessageElement.textContent = '';
        errorMessageElement.style.display = 'none';
    }
});
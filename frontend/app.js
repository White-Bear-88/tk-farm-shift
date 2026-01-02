document.addEventListener('DOMContentLoaded', function() {
    const app = document.getElementById('app');
    
    app.innerHTML = `
        <div>
            <h2>システム準備完了</h2>
            <p>酪農シフト管理システムが正常に動作しています。</p>
            <p>デプロイ時刻: ${new Date().toLocaleString('ja-JP')}</p>
        </div>
    `;
});
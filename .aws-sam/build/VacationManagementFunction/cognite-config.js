// CogniteID設定
const COGNITE_CONFIG = {
    // 開発環境用設定
    dev: {
        clientId: 'usr7wyygjep',
        redirectUri: 'http://localhost:8080/callback.html',
        cogniteDomain: 'https://your-cognite-domain.auth.region.amazoncognito.com',
        scope: 'openid profile email'
    },
    // 本番環境用設定
    prod: {
        clientId: 'usr7wyygjep',
        redirectUri: 'https://your-domain.com/callback.html',
        cogniteDomain: 'https://your-prod-cognite-domain.auth.region.amazoncognito.com',
        scope: 'openid profile email'
    }
};

// 現在の環境を判定
function getCurrentEnvironment() {
    return window.location.hostname === 'localhost' ? 'dev' : 'prod';
}

// 現在の設定を取得
function getCogniteConfig() {
    return COGNITE_CONFIG[getCurrentEnvironment()];
}
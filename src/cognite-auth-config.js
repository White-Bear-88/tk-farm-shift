// CogniteID認証設定
const COGNITE_AUTH_CONFIG = {
    // 環境変数から取得（本番環境では環境変数を設定）
    CLIENT_ID: process?.env?.COGNITE_CLIENT_ID || 'your-cognite-client-id',
    TENANT_DOMAIN: process?.env?.COGNITE_TENANT_DOMAIN || 'your-tenant.auth.region.amazoncognito.com',
    REDIRECT_URI: process?.env?.COGNITE_REDIRECT_URI || (
        window.location.hostname === 'localhost' 
            ? 'http://localhost:8080/callback.html'
            : 'https://your-domain.com/callback.html'
    ),
    SCOPE: 'openid profile email',
    RESPONSE_TYPE: 'id_token',
    
    // 環境判定
    IS_DEVELOPMENT: window.location.hostname === 'localhost' || window.location.hostname.includes('dev')
};

// 設定取得関数
function getCogniteConfig() {
    return COGNITE_AUTH_CONFIG;
}

// 開発環境判定
function isDevelopmentMode() {
    return COGNITE_AUTH_CONFIG.IS_DEVELOPMENT;
}
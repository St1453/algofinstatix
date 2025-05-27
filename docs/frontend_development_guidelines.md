# Flutter Development Guidelines & Best Practices

## Table of Contents
- [Recommended Packages](#recommended-packages)
- [Project Structure](#project-structure)
- [Navigation](#navigation)
- [Code Organization](#code-organization)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Error Handling](#error-handling)
- [Testing Strategy](#testing-strategy)
- [Performance Optimization](#performance-optimization)
- [Security](#security)
- [Git Workflow](#git-workflow)

## Recommended Packages

### Core Dependencies
```yaml
dependencies:
  # State Management & DI
  flutter_riverpod: ^2.4.9
  riverpod_annotation: ^2.3.3
  freezed_annotation: ^2.4.1

  # Navigation
  go_router: ^11.1.0
  auto_route: ^7.8.2

  # UI Components
  flutter_screenutil: ^5.9.0
  gap: ^3.0.1
  flutter_svg: ^2.0.10+1
  intl: ^0.18.1
  flutter_form_builder: ^9.2.2
  form_builder_validators: ^8.0.0

  # Finance-Specific
  fl_chart: ^0.65.0
  decimal: ^2.3.0
  money2: ^4.0.1
  yahoofin: ^0.2.0

  # Post Features
  flutter_markdown: ^0.6.18
  markdown_widget: ^7.0.0
  image_picker: ^1.0.7
  file_picker: ^6.1.1
  cached_network_image: ^3.3.0
  video_player: ^2.8.1
  chewie: ^1.7.4

  # API & Storage
  dio: ^5.3.2
  retrofit: ^4.1.0
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
```

### Development Dependencies
```yaml
dev_dependencies:
  build_runner: ^2.4.6
  freezed: ^2.4.5
  json_serializable: ^6.7.1
  retrofit_generator: ^5.0.3
  flutter_test:
    sdk: flutter
  mockito: ^5.4.4
  test: ^1.24.9
  flutter_lints: ^3.0.1
```

## Project Structure

### Feature-Based (DDD) Architecture

```
lib/
├── core/                             # Core functionality
│   ├── config/
│   │   ├── app_router.dart          # go_router configuration
│   │   └── theme.dart               # App theming
│   ├── errors/                      # Error handling
│   │   ├── error_handler.dart
│   │   └── error_widget.dart
│   └── utils/                       # Utilities
│       ├── constants.dart
│       └── extensions.dart
│
├── features/
│   └── auth/                        # Authentication feature
│       ├── data/                    # Data layer
│       │   ├── datasources/
│       │   │   └── auth_remote_data_source.dart
│       │   ├── models/
│       │   │   ├── login_request_model.dart
│       │   │   └── token_model.dart
│       │   └── repositories/
│       │       └── auth_repository_impl.dart
│       │
│       ├── domain/                  # Domain layer
│       │   ├── entities/
│       │   │   └── user_entity.dart
│       │   ├── repositories/
│       │   │   └── auth_repository.dart
│       │   └── usecases/
│       │       ├── login_usecase.dart
│       │       └── get_current_user_usecase.dart
│       │
│       └── presentation/            # Presentation layer
│           ├── blocs/               # State management
│           │   ├── auth_bloc.dart
│           │   ├── auth_event.dart
│           │   └── auth_state.dart
│           │
│           ├── pages/
│           │   ├── login_page.dart
│           │   └── register_page.dart
│           │
│           └── widgets/             # Reusable widgets
│               ├── login_form.dart
│               └── auth_dialog.dart
│
├── shared/                          # Shared components
│   ├── widgets/                     # Global widgets
│   ├── services/                    # Global services
│   └── theme/                       # Global theming
│
└── main.dart                        # Application entry point
```

### Key Components

#### Finance Module
```
features/
└── finance/
    ├── data/
    │   ├── datasources/
    │   │   ├── finance_remote_data_source.dart
    │   │   └── finance_local_data_source.dart
    │   ├── models/
    │   │   ├── stock_model.dart
    │   │   ├── portfolio_model.dart
    │   │   └── transaction_model.dart
    │   └── repositories/
    │       └── finance_repository_impl.dart
    ├── domain/
    │   ├── entities/
    │   ├── repositories/
    │   └── usecases/
    └── presentation/
        ├── bloc/
        ├── pages/
        │   ├── dashboard_page.dart
        │   ├── stock_detail_page.dart
        │   └── portfolio_page.dart
        └── widgets/
            ├── stock_chart.dart
            └── portfolio_summary.dart
```

#### Posts Module
```
features/
└── core_posts/                     # Reusable core posts feature
    ├── data/
    │   ├── models/
    │   │   ├── base_post_model.dart
    │   │   ├── base_comment_model.dart
    │   │   └── base_reaction_model.dart
    │   └── repositories/
    │       └── base_post_repository.dart
    ├── domain/
    │   ├── entities/
    │   └── repositories/
    └── presentation/
        └── widgets/
            ├── post_card.dart
            └── comment_section.dart
```

1. **Core Directory**
   - Contains app-wide configurations and utilities
   - Handles routing, theming, and error handling
   - Provides base classes and extensions

2. **Features Directory**
   - Each feature is self-contained with its own domain logic
   - Follows Clean Architecture principles
   - Contains all related components (data, domain, presentation)

3. **Shared Directory**
   - Contains reusable widgets and services
   - Houses global theming and styles
   - Provides utility functions and constants

4. **State Management**
   - Uses BLoC pattern for complex state
   - Implements Riverpod for dependency injection
   - Follows unidirectional data flow


## Finance-Specific Implementation

### Charts and Data Visualization
- Use `fl_chart` for interactive financial charts
- Implement `decimal` for precise decimal arithmetic
- Use `money2` for currency handling and formatting
- Fetch market data using `yahoofin` or similar packages

### State Management for Financial Data
```dart
@freezed
class StockState with _$StockState {
  const factory StockState({
    @Default(DataStatus.initial) DataStatus status,
    Stock? stock,
    List<CandleData>? historicalData,
    String? error,
  }) = _StockState;
}
```

## Generic Post Feature Architecture

### 1. Core Directory Structure
```
features/
└── core_posts/                    # Core post functionality
    ├── data/
    │   ├── datasources/           # Data sources (local/remote)
    │   ├── models/                # Data models
    │   └── repositories/           # Repository implementations
    ├── domain/
    │   ├── entities/             # Business entities
    │   ├── repositories/           # Abstract repositories
    │   └── usecases/               # Business logic
    └── presentation/
        ├── bloc/                  # State management
        ├── widgets/                # Reusable UI components
        └── pages/                  # Screens
```

### 2. Base Models

#### Base Post Model
```dart
@freezed
class BasePostModel with _$BasePostModel {
  const factory BasePostModel({
    required String id,
    required String title,
    required String content,
    required String authorId,
    required String authorName,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
    @Default([]) List<String> mediaUrls,
    @Default([]) List<String> tags,
    @Default(0) int likeCount,
    @Default(0) int commentCount,
    @Default(false) bool isLiked,
    @JsonKey(includeFromJson: false, includeToJson: false)
    @Default(PostStatus.published)
    PostStatus status,
  }) = _BasePostModel;

  factory BasePostModel.fromJson(Map<String, dynamic> json) =>
      _$$BasePostModelFromJson(json);
}

enum PostStatus { draft, published, archived }
```

#### Base Comment Model
```dart
@freezed
class BaseCommentModel with _$BaseCommentModel {
  const factory BaseCommentModel({
    required String id,
    required String postId,
    required String authorId,
    required String authorName,
    required String content,
    required DateTime createdAt,
    @Default([]) List<String> mentionedUserIds,
    @Default(0) int likeCount,
    @Default(false) bool isLiked,
  }) = _BaseCommentModel;

  factory BaseCommentModel.fromJson(Map<String, dynamic> json) =>
      _$$BaseCommentModelFromJson(json);
}
```

### 3. Repository Pattern

#### Repository Interface
```dart
abstract class PostRepository<T extends BasePostModel> {
  Future<List<T>> getPosts({
    int page = 1,
    int limit = 10,
    Map<String, dynamic>? filters,
  });
  
  Future<T> getPostById(String id);
  Future<T> createPost(T post);
  Future<T> updatePost(T post);
  Future<void> deletePost(String id);
  Future<void> reactToPost(String postId, String userId, String reactionType);
  Future<List<BaseCommentModel>> getPostComments(String postId);
  Future<BaseCommentModel> addComment(String postId, String content);
}
```

### 4. State Management with Riverpod

#### Post State
```dart
@freezed
class PostState<T extends BasePostModel> with _$PostState<T> {
  const factory PostState({
    @Default(PostStatus.initial) PostStatus status,
    @Default([]) List<T> posts,
    @Default(1) int page,
    @Default(false) bool hasReachedMax,
    String? error,
  }) = _PostState<T>;
}

enum PostStatus { initial, loading, success, failure, paginating }
```

#### Post Notifier
```dart
class PostNotifier<T extends BasePostModel> extends StateNotifier<PostState<T>> {
  final PostRepository<T> _repository;
  
  PostNotifier(this._repository) : super(const PostState.initial());

  Future<void> loadPosts({bool refresh = false}) async {
    if (!refresh) {
      state = state.copyWith(
        status: state.posts.isEmpty 
            ? PostStatus.loading 
            : PostStatus.paginating,
      );
    }

    try {
      final posts = await _repository.getPosts(
        page: state.page + 1,
      );
      
      state = state.copyWith(
        status: PostStatus.success,
        posts: [...state.posts, ...posts],
        hasReachedMax: posts.length < 10,
        page: state.page + 1,
      );
    } catch (e) {
      state = state.copyWith(
        status: PostStatus.failure,
        error: e.toString(),
      );
    }
  }
}
```

### 5. Reusable UI Components

#### Generic Post Card
```dart
class PostCard<T extends BasePostModel> extends ConsumerWidget {
  final T post;
  final Widget Function(BuildContext, T)? header;
  final Widget Function(BuildContext, T)? footer;
  final VoidCallback? onTap;
  final bool showReactions;

  const PostCard({
    required this.post,
    this.header,
    this.footer,
    this.onTap,
    this.showReactions = true,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 0),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (header != null) header!(context, post),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    post.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  MarkdownBody(data: post.content),
                ],
              ),
            ),
            if (showReactions) _buildReactionBar(post, ref),
            if (footer != null) footer!(context, post),
          ],
        ),
      ),
    );
  }
}
```

### 6. Context-Specific Implementations

#### Financial Post Example
```dart
// features/finance/posts/data/models/financial_post_model.dart
@freezed
class FinancialPostModel extends BasePostModel with _$FinancialPostModel {
  const FinancialPostModel._();
  
  const factory FinancialPostModel({
    // Base fields
    required String id,
    required String title,
    required String content,
    required String authorId,
    required String authorName,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
    @Default([]) List<String> mediaUrls,
    @Default([]) List<String> tags,
    @Default(0) int likeCount,
    @Default(0) int commentCount,
    @Default(false) bool isLiked,
    
    // Financial-specific fields
    required String tickerSymbol,
    required AnalysisType analysisType,
    required Map<String, dynamic> financialMetrics,
    required List<double> historicalData,
  }) = _FinancialPostModel;

  factory FinancialPostModel.fromJson(Map<String, dynamic> json) =>
      _$$FinancialPostModelFromJson(json);
}
```

### 7. Navigation with GoRouter

```dart
// core/routes/app_router.dart
final router = GoRouter(
  routes: [
    // Core posts route
    GoRoute(
      path: '/posts',
      builder: (context, state) => const PostListPage(),
      routes: [
        GoRoute(
          path: ':postId',
          builder: (context, state) {
            final postId = state.pathParameters['postId']!;
            return PostDetailPage(postId: postId);
          },
        ),
      ],
    ),
  ],
);
```

### 8. Best Practices

1. **Separation of Concerns**
   - Keep core post logic separate from business-specific logic
   - Use composition over inheritance for extending functionality

2. **Performance**
   - Implement pagination for post lists
   - Use `ListView.builder` with `itemExtent`
   - Cache network images with `cached_network_image`

3. **Accessibility**
   - Add semantic labels to interactive elements
   - Ensure proper contrast ratios
   - Support screen readers

4. **Testing**
   - Write unit tests for business logic
   - Add widget tests for UI components
   - Implement integration tests for critical flows

## Navigation

### Standard: go_router

#### Decision
- Use `go_router` as the standard navigation solution for all Flutter applications
- Avoid using `Navigator` directly, use `go_router` instead.

#### Key Benefits
1. Type-safe navigation with compile-time route checking
2. Deep linking support out of the box
3. Web URL support
4. Better state management integration
5. Improved navigation stack management

#### Implementation Guidelines
- Define all routes in a centralized location (e.g., `lib/core/routes/app_router.dart`)
- Use `context.pop()`. It is ideal for scenarios where you want to navigate back to the previous screen, such as closing a modal or detail page.
- Use `context.go()`. It is ideal for scenarios where you want to reset navigation history, such as after login, logout, or redirecting to a home page. It ensures the user cannot return to the previous screen.
- Use `context.push()`. It is ideal for scenarios where you want to navigate to a new screen while preserving the previous screen in the navigation stack. It is useful for modal dialogs, forms, or any other screen that should be accessible from the previous screen.
- Implement route guards for authentication
- Use `GoRouteData` for type-safe route parameters
- Handle web URLs and deep links

#### Example Usage
```dart
// Navigation example
context.go('/home');

// With parameters
context.go('/user/123', extra: {'from': 'dashboard'});

// Modal route
context.push('/modal');
```

#### Route Definition Example
```dart
// lib/core/routes/app_router.dart
import 'package:go_router/go_router.dart';
import 'package:your_app/features/home/presentation/home_page.dart';
import 'package:your_app/features/profile/presentation/profile_page.dart';
import 'package:your_app/features/auth/presentation/login_page.dart';

final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomePage(),
    ),
    GoRoute(
      path: '/profile/:userId',
      builder: (context, state) => ProfilePage(
        userId: state.pathParameters['userId']!,
      ),
    ),
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginPage(),
    ),
  ],
);
```

#### Route Guards Example
```dart
// Add this to your router configuration
redirect: (context, state) {
  final isLoggedIn = ref.watch(authProvider).isAuthenticated;
  final isLoginRoute = state.matchedLocation == '/login';
  
  if (!isLoggedIn && !isLoginRoute) {
    return '/login';
  }
  
  if (isLoggedIn && isLoginRoute) {
    return '/';
  }
  
  return null;
},
```

## Code Organization

### File Naming
- Use `snake_case` for all files
- Suffix files with purpose:
  - `_widget.dart` for reusable widgets
  - `_page.dart` for full screens
  - `_service.dart` for services
  - `_model.dart` for data models

### Import Pattern
```dart
// Core Flutter/Dart
import 'dart:async';
import 'package:flutter/material.dart';

// Third-party packages
import 'package:riverpod/riverpod.dart';

// Local imports (using barrel file)
import 'package:your_app/features/feature_index.dart';

// Relative imports (same directory only)
import './widgets/my_widget.dart';
```

## State Management

### Core Principles
- **Separation of Concerns**: Keep business logic in dedicated classes, separate from UI components
- **Single Source of Truth**: Ensure each piece of application state has a single authoritative source
- **Unidirectional Data Flow**: Data should flow in a single direction through the widget tree

### State Management Solutions

#### 1. Local State with Riverpod

##### When to Use Local State
- UI-only state that doesn't need to be shared across widgets
- Form states and validation
- Animation controllers
- Page/Section UI state
- Temporary UI state (e.g., expansion panels, tabs)

##### Implementation Approaches

###### 1. Using `StateProvider` for Simple State
```dart
// 1. Define a provider (can be in the same file or separate)
final counterProvider = StateProvider<int>((ref) => 0);

// 2. Use in widget
class CounterWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(counterProvider);
    
    return Column(
      children: [
        Text('Count: $count'),
        ElevatedButton(
          onPressed: () => ref.read(counterProvider.notifier).state++,
          child: const Text('Increment'),
        ),
      ],
    );
  }
}
```

###### 2. Using `StateNotifier` for Complex Local State
```dart
// 1. Define the state class
class FormState {
  final String email;
  final String password;
  final bool isLoading;
  final String? error;
  
  FormState({
    this.email = '',
    this.password = '',
    this.isLoading = false,
    this.error,
  });
  
  FormState copyWith({
    String? email,
    String? password,
    bool? isLoading,
    String? error,
  }) {
    return FormState(
      email: email ?? this.email,
      password: password ?? this.password,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

// 2. Create a StateNotifier
class FormNotifier extends StateNotifier<FormState> {
  FormNotifier() : super(FormState());
  
  void updateEmail(String value) {
    state = state.copyWith(email: value.trim(), error: null);
  }
  
  void updatePassword(String value) {
    state = state.copyWith(password: value, error: null);
  }
  
  Future<void> submit() async {
    if (state.isLoading) return;
    
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      // Simulate API call
      await Future.delayed(const Duration(seconds: 1));
      
      if (state.email.isEmpty || state.password.isEmpty) {
        throw Exception('Email and password are required');
      }
      
      // Handle successful submission
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }
}

// 3. Create provider
final formProvider = StateNotifierProvider.autoDispose<FormNotifier, FormState>(
  (ref) => FormNotifier(),
);

// 4. Use in widget
class LoginForm extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final form = ref.watch(formProvider);
    final notifier = ref.read(formProvider.notifier);
    
    return Form(
      child: Column(
        children: [
          if (form.error != null)
            Text(
              form.error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Email'),
            onChanged: notifier.updateEmail,
            enabled: !form.isLoading,
          ),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Password'),
            obscureText: true,
            onChanged: notifier.updatePassword,
            enabled: !form.isLoading,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: form.isLoading ? null : notifier.submit,
            child: form.isLoading
                ? const CircularProgressIndicator()
                : const Text('Sign In'),
          ),
        ],
      ),
    );
  }
}
```

###### 3. Using `StateProvider` with Async Operations
```dart
// 1. Define provider with async initialization
final userProfileProvider = FutureProvider.autoDispose((ref) async {
  // This will automatically handle loading/error states
  final userId = ref.watch(authProvider).userId;
  if (userId == null) throw Exception('Not authenticated');
  
  final userRepo = ref.watch(userRepositoryProvider);
  return await userRepo.getUserProfile(userId);
});

// 2. Use in widget
class ProfilePage extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userProfile = ref.watch(userProfileProvider);
    
    return userProfile.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => Center(child: Text('Error: $error')),
      data: (user) => ProfileView(user: user),
    );
  }
}
```

##### Best Practices for Local State
1. **Auto-dispose when possible**
   - Use `autoDispose` for temporary state that should be cleaned up
   ```dart
   final tempStateProvider = StateProvider.autoDispose<int>((ref) => 0);
   ```

2. **Combine providers for derived state**
   ```dart
   final filteredItemsProvider = Provider<List<Item>>((ref) {
     final items = ref.watch(itemsProvider);
     final filter = ref.watch(filterProvider);
     return items.where((item) => item.matches(filter)).toList();
   });
   ```

3. **Use `select` for performance**
   ```dart
   // Only rebuild when the username changes, not the entire user object
   final username = ref.watch(userProvider.select((user) => user?.username));
   ```

4. **Handle loading and error states**
   - Always handle loading and error states when working with async providers
   - Use `AsyncValue` for consistent error handling

5. **Keep providers focused**
   - Each provider should have a single responsibility
   - Split complex state into multiple providers when needed

6. **Testing**
   - Test state changes in isolation
   - Mock dependencies for unit tests
   - Test error states and edge cases

##### When to Use Local State vs Global State
- **Use Local State when:**
  - State is only needed in a single widget or its children
  - State is temporary and doesn't need to persist
  - State is UI-specific (e.g., form state, animation controllers)
  
- **Use Global State when:**
  - State needs to be shared across multiple screens
  - State needs to persist across navigation
  - State represents business logic or app state

##### Example: Form Validation
```dart
final signInFormProvider = StateNotifierProvider.autoDispose<SignInFormNotifier, SignInFormState>(
  (ref) => SignInFormNotifier(),
);

class SignInFormNotifier extends StateNotifier<SignInFormState> {
  SignInFormNotifier() : super(const SignInFormState());
  
  void updateEmail(String value) {
    state = state.copyWith(
      email: value.trim(),
      emailError: _validateEmail(value) ? null : 'Invalid email',
    );
  }
  
  void updatePassword(String value) {
    state = state.copyWith(
      password: value,
      passwordError: _validatePassword(value) ? null : 'Password too short',
    );
  }
  
  bool get isValid => 
      state.email.isNotEmpty &&
      state.password.isNotEmpty &&
      state.emailError == null &&
      state.passwordError == null;
  
  Future<void> submit() async {
    if (!isValid || state.isSubmitting) return;
    
    state = state.copyWith(isSubmitting: true);
    
    try {
      // Handle form submission
      await ref.read(authProvider.notifier).signIn(
        email: state.email,
        password: state.password,
      );
      
      // Handle success
    } catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: e.toString(),
      );
      rethrow;
    } finally {
      if (mounted) {
        state = state.copyWith(isSubmitting: false);
      }
    }
  }
  
  bool _validateEmail(String email) {
    return RegExp(r'^.+@[a-zA-Z]+\.[a-zA-Z]+(\.[a-zA-Z]+)?$').hasMatch(email);
  }
  
  bool _validatePassword(String password) => password.length >= 6;
}

@immutable
class SignInFormState {
  final String email;
  final String password;
  final String? emailError;
  final String? passwordError;
  final String? error;
  final bool isSubmitting;
  
  const SignInFormState({
    this.email = '',
    this.password = '',
    this.emailError,
    this.passwordError,
    this.error,
    this.isSubmitting = false,
  });
  
  SignInFormState copyWith({
    String? email,
    String? password,
    String? emailError,
    String? passwordError,
    String? error,
    bool? isSubmitting,
  }) {
    return SignInFormState(
      email: email ?? this.email,
      password: password ?? this.password,
      emailError: emailError,
      passwordError: passwordError,
      error: error,
      isSubmitting: isSubmitting ?? this.isSubmitting,
    );
  }
}
```

#### 2. Riverpod (Recommended for App State)
- **Why Riverpod?**
  - Compile-safe with no runtime exceptions
  - Excellent for dependency injection
  - Testable and mockable
  - Works well with both simple and complex state
  - Supports state persistence

##### Basic Usage
```dart
// Simple state
final counterProvider = StateProvider<int>((ref) => 0);

// StateNotifier for complex state
class CounterNotifier extends StateNotifier<int> {
  CounterNotifier() : super(0);
  
  void increment() => state++;
  void decrement() => state--;
  void reset() => state = 0;
}

final counterNotifierProvider = StateNotifierProvider<CounterNotifier, int>(
  (ref) => CounterNotifier(),
);

// Async state
final userProfileProvider = FutureProvider<UserProfile>((ref) async {
  final userId = ref.watch(authProvider).userId;
  return await ref.watch(userRepositoryProvider).getProfile(userId);
});

// Combined providers
final userPostsProvider = FutureProvider<List<Post>>((ref) async {
  final userId = ref.watch(authProvider).userId;
  final posts = await ref.watch(postRepositoryProvider).getUserPosts(userId);
  final favorites = ref.watch(favoritePostsProvider);
  
  return posts.map((post) => post.copyWith(
    isFavorite: favorites.any((fav) => fav.id == post.id),
  )).toList();
});
```

##### In Widgets
```dart
// Watching state
final counter = ref.watch(counterProvider);
final userProfile = ref.watch(userProfileProvider);

// Reading state without watching
final counter = ref.read(counterProvider.notifier);

// Handling loading/error states
return userProfile.when(
  loading: () => const CircularProgressIndicator(),
  error: (error, stack) => ErrorWidget(error),
  data: (user) => ProfileView(user: user),
);

// Updating state
ElevatedButton(
  onPressed: () => ref.read(counterProvider.notifier).increment(),
  child: const Text('Increment'),
);
```

##### Best Practices
- Keep providers small and focused
- Use `autoDispose` for temporary state
- Use `family` for parameterized providers
- Combine providers using `ref.watch` for derived state
- Use `select` to rebuild only when needed
```dart
// Only rebuild when username changes
final username = ref.watch(userProfileProvider.select((user) => user?.username));
```

### Best Practices

#### Initialization & Disposal
- Initialize controllers in `initState`
- Always dispose controllers in `dispose`
- Check `mounted` before calling `setState` after async operations

```dart
late final AnimationController _controller;

@override
void initState() {
  super.initState();
  _controller = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 1),
  )..forward();
}

@override
void dispose() {
  _controller.dispose();
  super.dispose();
}
```

#### Performance Optimization
- Use `const` constructors for widgets when possible
- Implement `==` and `hashCode` for state classes
- Use `const` constructors for immutable state objects

#### State Restoration
- Implement `restorable` properties for state that should survive app restarts
- Use `RestorableProperty` for simple values
- Consider `RestorableRouteFuture` for route state

### Error Handling
- Implement error boundaries for state changes
- Use `try/catch` blocks for async operations
- Provide meaningful error messages to users
- Log errors for debugging

### Testing State
- Test state changes in isolation
- Mock dependencies for unit tests
- Use `pumpAndSettle` for testing animations
- Test error states and edge cases

## API Integration

### Request/Response Pattern
```dart
{
  "success": boolean,
  "data": {},
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly message"
  }
}
```

### Error Handling
- Implement global error handling
- Show user-friendly error messages
- Log detailed errors for debugging
- Handle network and timeout scenarios

## Testing Strategy

### Unit Tests
- Test business logic in isolation
- Mock external dependencies
- Follow Given-When-Then pattern
- Aim for 80%+ test coverage

### Widget Tests
- Test widget rendering
- Test user interactions
- Test error states
- Use `pumpAndSettle` for animations

## Performance Optimization

### Build Methods
- Use `const` constructors
- Break down large widgets
- Use `ListView.builder` for long lists
- Optimize image loading and caching

### State Management
- Minimize `setState` calls
- Use `const` widgets
- Implement proper disposal
- Use `RepaintBoundary` for complex animations

## Security

### Data Protection
- Never hardcode sensitive information
- Use environment variables
- Encrypt sensitive data
- Implement proper session management

### Input Validation
- Validate all inputs
- Sanitize user content
- Use HTTPS for all API calls
- Implement proper CORS policies

## Git Workflow

### Branching Strategy
- Use feature branches
- Follow naming convention: `feature/description`
- Keep branches small and focused
- Delete merged branches

### Commit Messages
- Write clear, concise messages
- Use present tense
- Follow Conventional Commits
- Reference issues/tickets

## AI-Assisted Development

### Best Practices
- Review all AI-generated code
- Use AI for boilerplate and repetitive tasks
- Maintain clear feature boundaries
- Document AI usage in code comments
- Regularly update AI context with project changes

### Windsurf Commands
- Use predefined prompts for common tasks
- Create custom snippets for repetitive patterns
- Leverage AI for code reviews and refactoring
- Use AI for test generation

---
*Last Updated: 2025-05-19*
